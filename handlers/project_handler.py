from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectResponse(BaseModel):
    """Response model for a project."""
    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    created_at: str = Field(..., description="Timestamp when the project was created")
    updated_at: str | None = Field(None, description="Timestamp when the project was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "proj_123",
                "name": "My RAG Project",
                "created_at": "2024-01-15 10:30:00",
                "updated_at": "2024-01-16 14:20:00"
            }
        }


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., description="Project name", min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My RAG Project"
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted project")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "proj_123"
            }
        }


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a new project",
    description="Create a new project with the given name.",
    response_description="The created project with generated ID and timestamps",
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My RAG Project",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid request (e.g., missing name or duplicate name)",
            "content": {
                "application/json": {
                    "example": {"detail": "UNIQUE constraint failed: projects.name"}
                }
            }
        }
    }
)
async def create_project(project: ProjectCreateRequest, request: Request):
    """
    Create a new project.

    The project ID and timestamps are automatically generated.
    Project names must be unique across the system.

    Args:
        project: Project creation data with name

    Returns:
        The created project with ID, name, and timestamps

    Raises:
        HTTPException: 400 if project name already exists
    """
    try:
        created_project = request.app.state.store.project_repo.create({"name": project.name})
        return created_project
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="Get all projects",
    description="Retrieve a list of all projects in the system.",
    response_description="List of all projects with their details"
)
async def get_all_projects(request: Request):
    """
    Retrieve all projects.

    Returns a list of all projects with their IDs, names, and timestamps.
    """
    projects = request.app.state.store.project_repo.get_all()
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a single project by its ID.",
    response_description="Project details",
    responses={
        200: {
            "description": "Project found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My RAG Project",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": None
                    }
                }
            }
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 'proj_123' not found"}
                }
            }
        }
    }
)
async def get_project_by_id(project_id: str, request: Request):
    """
    Retrieve a project by ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        The project with ID, name, and timestamps

    Raises:
        HTTPException: 404 if project not found
    """
    project = request.app.state.store.project_repo.get_by_id(project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id '{project_id}' not found"
        )

    return project


@router.delete(
    "/{project_id}",
    response_model=DeleteResponse,
    summary="Delete a project",
    description="Delete a project by its ID. This will cascade delete all related data.",
    response_description="Deletion status and project ID",
    responses={
        200: {
            "description": "Project deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "id": "proj_123"}
                }
            }
        },
        404: {
            "description": "Project not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Project with id 'proj_123' not found"}
                }
            }
        }
    }
)
async def delete_project(project_id: str, request: Request):
    """
    Delete a project by ID.

    This operation will cascade delete all related data including:
    - Tests
    - Corpus items
    - Question-answer pairs
    - Evaluations

    Args:
        project_id: The unique identifier of the project to delete

    Returns:
        Deletion confirmation with the project ID

    Raises:
        HTTPException: 404 if project not found
    """
    success = request.app.state.store.project_repo.delete_by_id(project_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id '{project_id}' not found"
        )

    return {"deleted": True, "id": project_id}
