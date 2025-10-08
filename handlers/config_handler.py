from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import Optional

router = APIRouter(prefix="/configs", tags=["Configs"])


class ConfigResponse(BaseModel):
    """Response model for a config."""
    id: str = Field(..., description="Unique config identifier")
    test_id: str = Field(..., description="Associated test ID")
    type: str = Field(..., description="Config type, either 'semantic' or 'recursive'")
    chunk_size: int = Field(..., description="Chunk size", ge=0, le=5000)
    overlap: int = Field(..., description="Overlap", ge=0, le=500)
    generative_model: str = Field(..., description="Generative model name")
    embedding_model: str = Field(..., description="Embedding model name")
    top_k: int = Field(..., description="Top K value", ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "config_123",
                "test_id": "test_123",
                "type": "semantic",
                "chunk_size": 1000,
                "overlap": 100,
                "generative_model": "openai_4o",
                "embedding_model": "openai_text_embedding_large_3",
                "top_k": 10
            }
        }


class ConfigCreateRequest(BaseModel):
    """Request model for creating a config."""
    test_id: str = Field(..., description="Test ID", min_length=1)
    type: str = Field(..., description="Config type", pattern=r"^(semantic|recursive)$")
    chunk_size: int = Field(..., description="Chunk size", ge=0, le=5000)
    overlap: int = Field(..., description="Overlap", ge=0, le=500)
    generative_model: str = Field("openai_4o", description="Generative model name")
    embedding_model: str = Field("openai_text_embedding_large_3", description="Embedding model name")
    top_k: int = Field(10, description="Top K value", ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "test_123",
                "type": "semantic",
                "chunk_size": 1000,
                "overlap": 100,
                "generative_model": "openai_4o",
                "embedding_model": "openai_text_embedding_large_3",
                "top_k": 10
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    test_id: str = Field(..., description="Test ID of the deleted config")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "test_id": "test_123"
            }
        }


@router.post(
    "",
    response_model=ConfigResponse,
    status_code=201,
    summary="Create a new config",
    description="Create a new config for a test. Ensures only one config per test.",
    response_description="The created config with generated ID",
    responses={
        201: {
            "description": "Config created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "test_id": "test_123",
                        "type": "semantic",
                        "chunk_size": 1000,
                        "overlap": 100,
                        "generative_model": "openai_4o",
                        "embedding_model": "openai_text_embedding_large_3",
                        "top_k": 10
                    }
                }
            }
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input"}
                }
            }
        }
    }
)
async def create_config(config: ConfigCreateRequest, request: Request):
    """
    Create a new config.

    The config ID is automatically generated.
    Only one config per test is allowed; existing config is replaced.

    Args:
        config: Config creation data

    Returns:
        The created config

    Raises:
        HTTPException: 400 if invalid data
    """
    try:
        created_config = request.app.state.store.config_repo.create(config.dict())
        return created_config
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/{test_id}",
    response_model=ConfigResponse,
    summary="Get config by test ID",
    description="Retrieve the config for a given test ID.",
    response_description="The config details",
    responses={
        200: {
            "description": "Config retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "config_123",
                        "test_id": "test_123",
                        "type": "semantic",
                        "chunk_size": 1000,
                        "overlap": 100,
                        "generative_model": "openai_4o",
                        "embedding_model": "openai_text_embedding_large_3",
                        "top_k": 10
                    }
                }
            }
        },
        404: {
            "description": "Config not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Config not found"}
                }
            }
        }
    }
)
async def get_config_by_test_id(test_id: str, request: Request):
    """
    Retrieve config for a test.

    Args:
        test_id: The unique identifier of the test

    Returns:
        The config for the test

    Raises:
        HTTPException: 404 if config not found
    """
    config = request.app.state.store.config_repo.get_by_test_id(test_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Config not found"
        )

    return config


@router.delete(
    "/{test_id}",
    response_model=DeleteResponse,
    summary="Delete config by test ID",
    description="Delete the config associated with a given test ID.",
    response_description="Deletion status and test ID",
    responses={
        200: {
            "description": "Config deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "test_id": "test_123"}
                }
            }
        },
        404: {
            "description": "Config not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Config not found"}
                }
            }
        }
    }
)
async def delete_config_by_test_id(test_id: str, request: Request):
    """
    Delete config by test ID.

    Args:
        test_id: The unique identifier of the test

    Returns:
        Deletion confirmation with the test ID

    Raises:
        HTTPException: 404 if config not found
    """
    success = request.app.state.store.config_repo.delete_by_test_id(test_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Config not found"
        )

    return {"deleted": True, "test_id": test_id}
