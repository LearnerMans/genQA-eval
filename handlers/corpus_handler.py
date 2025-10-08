from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/corpus", tags=["Corpus"])


class CorpusResponse(BaseModel):
    """Response model for a corpus."""
    id: str = Field(..., description="Unique corpus identifier")
    project_id: str = Field(..., description="Project ID this corpus belongs to")
    name: str = Field(..., description="Corpus name")
    created_at: str = Field(..., description="Timestamp when the corpus was created")
    updated_at: Optional[str] = Field(None, description="Timestamp when the corpus was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "corpus_123",
                "project_id": "proj_456",
                "name": "My Corpus",
                "created_at": "2024-01-15 10:30:00",
                "updated_at": "2024-01-16 14:20:00"
            }
        }


class CorpusCreateRequest(BaseModel):
    """Request model for creating a corpus."""
    project_id: str = Field(..., description="Project ID to associate the corpus with")
    name: str = Field("Default Corpus", description="Corpus name", min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_456",
                "name": "My Corpus"
            }
        }


class CorpusUpdateRequest(BaseModel):
    """Request model for updating a corpus."""
    name: Optional[str] = Field(None, description="New corpus name", min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Corpus Name"
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted corpus")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "corpus_123"
            }
        }


@router.post(
    "",
    response_model=CorpusResponse,
    status_code=201,
    summary="Create a new corpus",
    description="Create a new corpus for a project. Each project can have only one corpus.",
    response_description="The created corpus with generated ID and timestamps",
    responses={
        201: {
            "description": "Corpus created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "project_id": "proj_456",
                        "name": "My Corpus",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid request (e.g., project already has a corpus)",
            "content": {
                "application/json": {
                    "example": {"detail": "Project already has a corpus"}
                }
            }
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 'proj_456' not found"}
                }
            }
        }
    }
)
async def create_corpus(corpus: CorpusCreateRequest, request: Request):
    """
    Create a new corpus for a project.

    Each project can have only one corpus. If the project already has a corpus,
    this operation will fail.

    Args:
        corpus: Corpus creation data with project_id and name

    Returns:
        The created corpus with ID, project_id, name, and timestamps

    Raises:
        HTTPException: 400 if project already has a corpus or invalid data
        HTTPException: 404 if project not found
    """
    try:
        # Check if project already has a corpus
        existing_corpus = request.app.state.store.corpus_repo.get_by_project_id(corpus.project_id)
        if existing_corpus:
            raise HTTPException(
                status_code=400,
                detail="Project already has a corpus"
            )

        created_corpus = request.app.state.store.corpus_repo.create({
            "project_id": corpus.project_id,
            "name": corpus.name
        })
        return created_corpus
    except Exception as e:
        if "Project already has a corpus" in str(e):
            raise e
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/project/{project_id}",
    response_model=CorpusResponse,
    summary="Get corpus by project ID",
    description="Retrieve the corpus associated with a specific project.",
    response_description="The corpus data for the project",
    responses={
        200: {
            "description": "Corpus found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "corpus_123",
                        "project_id": "proj_456",
                        "name": "My Corpus",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": "2024-01-16 14:20:00"
                    }
                }
            }
        },
        404: {
            "description": "Corpus not found for the project",
            "content": {
                "application/json": {
                    "example": {"detail": "No corpus found for project 'proj_456'"}
                }
            }
        }
    }
)
async def get_corpus_by_project_id(project_id: str, request: Request):
    """
    Get corpus by project ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        The corpus data for the project

    Raises:
        HTTPException: 404 if no corpus found for the project
    """
    corpus = request.app.state.store.corpus_repo.get_by_project_id(project_id)

    if not corpus:
        raise HTTPException(
            status_code=404,
            detail=f"No corpus found for project '{project_id}'"
        )

    return corpus


@router.get(
    "/{corpus_id}",
    response_model=CorpusResponse,
    summary="Get corpus by ID",
    description="Retrieve a corpus by its unique identifier.",
    response_description="The corpus data",
    responses={
        200: {
            "description": "Corpus found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "corpus_123",
                        "project_id": "proj_456",
                        "name": "My Corpus",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": "2024-01-16 14:20:00"
                    }
                }
            }
        },
        404: {
            "description": "Corpus not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Corpus with id 'corpus_123' not found"}
                }
            }
        }
    }
)
async def get_corpus_by_id(corpus_id: str, request: Request):
    """
    Get corpus by ID.

    Args:
        corpus_id: The unique identifier of the corpus

    Returns:
        The corpus data

    Raises:
        HTTPException: 404 if corpus not found
    """
    corpus = request.app.state.store.corpus_repo.get_by_id(corpus_id)

    if not corpus:
        raise HTTPException(
            status_code=404,
            detail=f"Corpus with id '{corpus_id}' not found"
        )

    return corpus


@router.get(
    "",
    response_model=List[CorpusResponse],
    summary="Get all corpora",
    description="Retrieve a list of all corpora in the system.",
    response_description="List of all corpora with their details"
)
async def get_all_corpora(request: Request):
    """
    Retrieve all corpora.

    Returns a list of all corpora with their IDs, project_ids, names, and timestamps.
    """
    corpora = request.app.state.store.corpus_repo.get_all()
    return corpora


@router.put(
    "/{corpus_id}",
    response_model=CorpusResponse,
    summary="Update a corpus",
    description="Update corpus information by its ID.",
    response_description="The updated corpus data",
    responses={
        200: {
            "description": "Corpus updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "corpus_123",
                        "project_id": "proj_456",
                        "name": "Updated Corpus Name",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": "2024-01-16 14:20:00"
                    }
                }
            }
        },
        404: {
            "description": "Corpus not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Corpus with id 'corpus_123' not found"}
                }
            }
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {"detail": "No valid fields to update"}
                }
            }
        }
    }
)
async def update_corpus(corpus_id: str, corpus_update: CorpusUpdateRequest, request: Request):
    """
    Update corpus by ID.

    Args:
        corpus_id: The unique identifier of the corpus to update
        corpus_update: The fields to update

    Returns:
        The updated corpus data

    Raises:
        HTTPException: 404 if corpus not found
        HTTPException: 400 if no valid fields to update
    """
    try:
        updated_corpus = request.app.state.store.corpus_repo.update(corpus_id, corpus_update.dict(exclude_unset=True))

        if not updated_corpus:
            raise HTTPException(
                status_code=404,
                detail=f"Corpus with id '{corpus_id}' not found"
            )

        return updated_corpus
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete(
    "/{corpus_id}",
    response_model=DeleteResponse,
    summary="Delete a corpus",
    description="Delete a corpus by its ID.",
    response_description="Deletion status and corpus ID",
    responses={
        200: {
            "description": "Corpus deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "id": "corpus_123"}
                }
            }
        },
        404: {
            "description": "Corpus not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Corpus with id 'corpus_123' not found"}
                }
            }
        }
    }
)
async def delete_corpus(corpus_id: str, request: Request):
    """
    Delete a corpus by ID.

    Args:
        corpus_id: The unique identifier of the corpus to delete

    Returns:
        Deletion confirmation with the corpus ID

    Raises:
        HTTPException: 404 if corpus not found
    """
    success = request.app.state.store.corpus_repo.delete_by_id(corpus_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Corpus with id '{corpus_id}' not found"
        )

    return {"deleted": True, "id": corpus_id}


@router.delete(
    "/project/{project_id}",
    response_model=DeleteResponse,
    summary="Delete corpus by project ID",
    description="Delete the corpus associated with a specific project.",
    response_description="Deletion status and corpus ID",
    responses={
        200: {
            "description": "Corpus deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "id": "corpus_123"}
                }
            }
        },
        404: {
            "description": "Corpus not found for the project",
            "content": {
                "application/json": {
                    "example": {"detail": "No corpus found for project 'proj_456'"}
                }
            }
        }
    }
)
async def delete_corpus_by_project_id(project_id: str, request: Request):
    """
    Delete corpus by project ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        Deletion confirmation with the corpus ID

    Raises:
        HTTPException: 404 if no corpus found for the project
    """
    # First check if corpus exists
    corpus = request.app.state.store.corpus_repo.get_by_project_id(project_id)
    if not corpus:
        raise HTTPException(
            status_code=404,
            detail=f"No corpus found for project '{project_id}'"
        )

    success = request.app.state.store.corpus_repo.delete_by_project_id(project_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No corpus found for project '{project_id}'"
        )

    return {"deleted": True, "id": corpus["id"]}
