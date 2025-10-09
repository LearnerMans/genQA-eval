from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/prompts", tags=["Prompts"])


class PromptResponse(BaseModel):
    """Response model for a prompt."""
    id: str = Field(..., description="Unique prompt identifier")
    test_id: str = Field(..., description="The id of the related test")
    name: str = Field(..., description="Prompt name")
    prompt: str = Field(..., description="Prompt text")
    created_at: str = Field(..., description="Timestamp when the prompt was created")
    updated_at: str | None = Field(None, description="Timestamp when the prompt was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "prompt_123",
                "test_id": "test_123",
                "name": "General QA Prompt",
                "prompt": "What is the capital of France?",
                "created_at": "2024-01-15 10:30:00",
                "updated_at": "2024-01-16 14:20:00"
            }
        }


class PromptCreateRequest(BaseModel):
    """Request model for creating a prompt."""
    name: str = Field(..., description="Prompt name", min_length=1, max_length=255)
    prompt: str = Field(..., description="Prompt text", min_length=1)
    test_id: str = Field(..., description="Test ID", min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "General QA Prompt",
                "prompt": "What is the capital of France?",
                "test_id": "test_123"
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "prompt_123"
            }
        }


@router.post(
    "",
    response_model=PromptResponse,
    status_code=201,
    summary="Create a new prompt",
    description="Create a new prompt with the given text.",
    response_description="The created prompt with generated ID and timestamps",
    responses={
        201: {
            "description": "Prompt created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "test_id": "test_123",
                        "name": "General QA Prompt",
                        "prompt": "What is the capital of France?",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "FOREIGN KEY constraint failed"}
                }
            }
        }
    }
)
async def create_prompt(prompt: PromptCreateRequest, request: Request):
    """
    Create a new prompt.

    The prompt ID and timestamps are automatically generated.

    Args:
        prompt: Prompt creation data with text and test_id

    Returns:
        The created prompt with ID, text, and timestamps

    Raises:
        HTTPException: 400 if test_id is invalid or prompt creation fails
    """
    try:
        created_prompt = request.app.state.store.prompt_repo.create({"name": prompt.name, "prompt": prompt.prompt, "test_id": prompt.test_id})
        return created_prompt
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[PromptResponse],
    summary="Get all prompts",
    description="Retrieve a list of all prompts in the system.",
    response_description="List of all prompts with their details"
)
async def get_all_prompts(request: Request):
    """
    Retrieve all prompts.

    Returns a list of all prompts with their IDs, text, and timestamps.
    """
    prompts = request.app.state.store.prompt_repo.get_all()
    return prompts


@router.get(
    "/test/{test_id}",
    response_model=List[PromptResponse],
    summary="Get prompts by test",
    description="Retrieve a list of prompts for a specific test.",
    response_description="List of prompts scoped to a test"
)
async def get_prompts_by_test(test_id: str, request: Request):
    """
    Retrieve all prompts for the given test_id.

    Args:
        test_id: The test identifier to filter prompts

    Returns:
        List of prompts for the specified test
    """
    prompts = request.app.state.store.prompt_repo.get_by_test_id(test_id)
    return prompts


@router.delete(
    "/{prompt_id}",
    response_model=DeleteResponse,
    summary="Delete a prompt",
    description="Delete a prompt by its ID.",
    response_description="Deletion status and prompt ID",
    responses={
        200: {
            "description": "Prompt deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "id": "prompt_123"}
                }
            }
        },
        404: {
            "description": "Prompt not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Prompt with id 'prompt_123' not found"}
                }
            }
        }
    }
)
async def delete_prompt(prompt_id: str, request: Request):
    """
    Delete a prompt by ID.

    Args:
        prompt_id: The unique identifier of the prompt to delete

    Returns:
        Deletion confirmation with the prompt ID

    Raises:
        HTTPException: 404 if prompt not found
    """
    success = request.app.state.store.prompt_repo.delete_by_id(prompt_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt with id '{prompt_id}' not found"
        )

    return {"deleted": True, "id": prompt_id}
