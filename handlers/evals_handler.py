import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from handlers.websocket_handler import evaluation_manager
from services.rag_eval_service import RAGEvalService
from llm.openai_llm import OpenAILLM
from llm.openai_embeddings import OpenAIEmbeddings

router = APIRouter(prefix="/evals", tags=["Evaluations"])

logger = logging.getLogger(__name__)


class EvalResponse(BaseModel):
    id: str
    test_run_id: str
    qa_pair_id: str
    bleu: float | None = None
    rouge: float | None = None
    answer_relevance: float | None = None
    context_relevance: float | None = None
    groundedness: float | None = None
    answer: str | None = None

class EvalRunRequest(BaseModel):
    """Request payload to trigger an evaluation for a single QA pair."""
    test_run_id: str
    qa_pair_id: str
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    eval_model: Optional[str] = None
    prompt_override: Optional[str] = None

class EvalRunStartResponse(BaseModel):
    """Response model for evaluation trigger acknowledgement."""
    status: str
    message: str | None = None

_active_evaluations: Dict[str, Dict[str, asyncio.Task]] = {}

def _register_evaluation_task(test_run_id: str, qa_pair_id: str, task: asyncio.Task) -> None:
    """Track active evaluation tasks to prevent duplicates."""
    run_tasks = _active_evaluations.setdefault(test_run_id, {})
    run_tasks[qa_pair_id] = task

    def _cleanup(_task: asyncio.Task) -> None:
        run_entry = _active_evaluations.get(test_run_id)
        if not run_entry:
            return
        run_entry.pop(qa_pair_id, None)
        if not run_entry:
            _active_evaluations.pop(test_run_id, None)

        if _task.cancelled():
            logger.info("Evaluation task cancelled for run %s, QA %s", test_run_id, qa_pair_id)
        elif _task.exception():
            logger.error("Evaluation task failed for run %s, QA %s: %s", test_run_id, qa_pair_id, _task.exception())

    task.add_done_callback(_cleanup)

async def _broadcast_evaluation_event(
    test_id: str,
    test_run_id: str,
    qa_pair_id: str,
    payload: Dict[str, Any]
) -> None:
    """Send evaluation event to all subscribers of the run and test."""
    message = {
        "type": "evaluation_progress",
        "test_id": test_id,
        "test_run_id": test_run_id,
        "qa_pair_id": qa_pair_id,
        **payload
    }
    await evaluation_manager.broadcast_to_run(test_run_id, message)
    await evaluation_manager.broadcast_to_test(test_id, message)


@router.get("/run/{test_run_id}", response_model=List[EvalResponse])
async def get_evals_by_run(test_run_id: str, request: Request):
    evals = request.app.state.store.eval_repo.get_by_test_run_id(test_run_id)
    return evals


@router.post("/run", response_model=EvalRunStartResponse, status_code=202)
async def run_single_evaluation(request: Request, data: EvalRunRequest):
    """Trigger evaluation for a single QA pair within a test run."""
    store = request.app.state.store

    # Lookup run and related config/prompt
    test_run = store.test_run_repo.get_by_id(data.test_run_id)
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    test = store.test_repo.get_by_id(test_run["test_id"])
    if not test:
        raise HTTPException(status_code=400, detail="Test associated with run not found")

    qa = store.qa_repo.get_by_id(data.qa_pair_id)
    if not qa:
        raise HTTPException(status_code=404, detail="QA pair not found")

    if qa["project_id"] != test["project_id"]:
        raise HTTPException(status_code=400, detail="QA pair does not belong to the same project as the test")

    config = store.config_repo.get_by_id(test_run["config_id"])
    if not config:
        # Fallback to config lookup by test_id for legacy runs
        config = store.config_repo.get_by_test_id(test_run["test_id"])
    if not config:
        raise HTTPException(status_code=400, detail="Configuration not found for test run")

    prompt_text = data.prompt_override
    if not prompt_text and test_run.get("prompt_id"):
        prompt = store.prompt_repo.get_by_id(test_run["prompt_id"])
        prompt_text = prompt["prompt"] if prompt else None

    top_k = data.top_k or config.get("top_k") or 10
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k must be positive")

    temperature = 0.0 if data.temperature is None else data.temperature
    eval_model = data.eval_model or "gpt-5"

    collection_name = f"test_{test_run['test_id']}_{config['embedding_model']}"

    # Prevent duplicate evaluations running simultaneously
    existing_task = _active_evaluations.get(data.test_run_id, {}).get(data.qa_pair_id)
    if existing_task and not existing_task.done():
        raise HTTPException(status_code=409, detail="Evaluation already in progress for this QA pair")

    llm = OpenAILLM(model_name=config.get("generative_model", "openai_4o"))
    embeddings = OpenAIEmbeddings(model_name=config.get("embedding_model", "openai_text_embedding_large_3"))
    service = RAGEvalService(
        db=request.app.state.db,
        vector_db=request.app.state.vdb,
        llm=llm,
        embeddings=embeddings
    )

    async def progress_callback(event: Dict[str, Any]) -> None:
        await _broadcast_evaluation_event(
            test_id=test["id"],
            test_run_id=data.test_run_id,
            qa_pair_id=data.qa_pair_id,
            payload={
                "event": "progress",
                "stage": event.get("stage"),
                "status": event.get("status"),
                "data": event.get("data"),
                "error": event.get("error")
            }
        )

    async def execute_evaluation() -> None:
        await _broadcast_evaluation_event(
            test_id=test["id"],
            test_run_id=data.test_run_id,
            qa_pair_id=data.qa_pair_id,
            payload={
                "event": "status",
                "status": "queued"
            }
        )

        try:
            await _broadcast_evaluation_event(
                test_id=test["id"],
                test_run_id=data.test_run_id,
                qa_pair_id=data.qa_pair_id,
                payload={
                    "event": "status",
                    "status": "running"
                }
            )

            result = await service.generate_and_evaluate(
                test_run_id=data.test_run_id,
                qa_pair_id=data.qa_pair_id,
                query=qa["question"],
                reference_answer=qa["answer"],
                collection_name=collection_name,
                top_k=top_k,
                prompt_template=prompt_text,
                temperature=temperature,
                eval_model=eval_model,
                progress_callback=progress_callback
            )

            await _broadcast_evaluation_event(
                test_id=test["id"],
                test_run_id=data.test_run_id,
                qa_pair_id=data.qa_pair_id,
                payload={
                    "event": "completed",
                    "status": "completed",
                    "result": result
                }
            )
        except Exception as exc:  # pragma: no cover - runtime errors surfaced to clients
            logger.exception("Evaluation failed for run %s QA %s", data.test_run_id, data.qa_pair_id)
            await _broadcast_evaluation_event(
                test_id=test["id"],
                test_run_id=data.test_run_id,
                qa_pair_id=data.qa_pair_id,
                payload={
                    "event": "error",
                    "status": "failed",
                    "error": str(exc)
                }
            )

    task = asyncio.create_task(execute_evaluation())
    _register_evaluation_task(data.test_run_id, data.qa_pair_id, task)

    return EvalRunStartResponse(status="queued", message="Evaluation started")
