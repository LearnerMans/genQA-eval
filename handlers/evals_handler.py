from fastapi import APIRouter, Request
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/evals", tags=["Evaluations"])


class EvalResponse(BaseModel):
    id: str
    test_run_id: str
    qa_pair_id: str
    bleu: float | None = None
    rouge: float | None = None
    answer_relevance: float | None = None
    context_relevance: float | None = None
    groundedness: float | None = None


@router.get("/run/{test_run_id}", response_model=List[EvalResponse])
async def get_evals_by_run(test_run_id: str, request: Request):
    evals = request.app.state.store.eval_repo.get_by_test_run_id(test_run_id)
    return evals

