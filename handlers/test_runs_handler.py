from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/test-runs", tags=["Test Runs"])


class TestRunResponse(BaseModel):
    id: str
    test_id: str
    config_id: str
    prompt_id: str | None = None


class TestRunCreateRequest(BaseModel):
    test_id: str = Field(..., min_length=1)
    prompt_id: str | None = Field(None, description="Prompt to lock this run to")


@router.get("/test/{test_id}", response_model=List[TestRunResponse])
async def get_runs_by_test(test_id: str, request: Request):
    runs = request.app.state.store.test_run_repo.get_by_test_id(test_id)
    return runs


@router.post("", response_model=TestRunResponse, status_code=201)
async def create_test_run(data: TestRunCreateRequest, request: Request):
    # Ensure config exists for test
    cfg = request.app.state.store.config_repo.get_by_test_id(data.test_id)
    if not cfg:
        raise HTTPException(status_code=400, detail="Config not found for test. Please create config first.")

    created = request.app.state.store.test_run_repo.create(
        {"test_id": data.test_id, "config_id": cfg["id"], "prompt_id": data.prompt_id}
    )
    return created

