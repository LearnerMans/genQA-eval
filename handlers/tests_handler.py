from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tests", tags=["Tests"])


class TestResponse(BaseModel):
    """Response model for a test."""
    id: str = Field(..., description="Unique test identifier")
    project_id: str = Field(...,description="the id of the related project")
    name: str = Field(..., description="Test name")
    created_at: str = Field(..., description="Timestamp when the test was created")
    updated_at: str | None = Field(None, description="Timestamp when the test was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "test_123",
                "project_id":"project123",
                "name": "My Test",
                "created_at": "2024-01-15 10:30:00",
                "updated_at": "2024-01-16 14:20:00"
            }
        }


class TestCreateRequest(BaseModel):
    """Request model for creating a test."""
    name: str = Field(..., description="Test name", min_length=1, max_length=255)
    project_id: str = Field(..., description="Project ID", min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Test",
                "project_id": "project123"
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted test")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "test_123"
            }
        }


@router.post(
    "",
    response_model=TestResponse,
    status_code=201,
    summary="Create a new test",
    description="Create a new test with the given name.",
    response_description="The created test with generated ID and timestamps",
    responses={
        201: {
            "description": "Test created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My Test",
                        "project_id":"project123",
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
                    "example": {"detail": "UNIQUE constraint failed: tests.name"}
                }
            }
        }
    }
)
async def create_test(test: TestCreateRequest, request: Request):
    """
    Create a new test.

    The test ID and timestamps are automatically generated.
    Test names must be unique across the system.

    Args:
        test: Test creation data with name

    Returns:
        The created test with ID, name, and timestamps

    Raises:
        HTTPException: 400 if test name already exists
    """
    try:
        created_test = request.app.state.store.test_repo.create({"name": test.name, "project_id":test.project_id})
        return created_test
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[TestResponse],
    summary="Get all tests",
    description="Retrieve a list of all tests in the system.",
    response_description="List of all tests with their details"
)
async def get_all_tests(request: Request):
    """
    Retrieve all tests.

    Returns a list of all tests with their IDs, names, and timestamps.
    """
    tests = request.app.state.store.test_repo.get_all()
    return tests


@router.get(
    "/project/{project_id}",
    response_model=List[TestResponse],
    summary="Get tests by project",
    description="Retrieve a list of tests for a specific project.",
    response_description="List of tests scoped to a project"
)
async def get_tests_by_project(project_id: str, request: Request):
    """
    Retrieve all tests for the given project_id.

    Args:
        project_id: The project identifier to filter tests

    Returns:
        List of tests for the specified project
    """
    tests = request.app.state.store.test_repo.get_by_project_id(project_id)
    return tests


@router.delete(
    "/{test_id}",
    response_model=DeleteResponse,
    summary="Delete a test",
    description="Delete a test by its ID.",
    response_description="Deletion status and test ID",
    responses={
        200: {
            "description": "Test deleted successfully",
            "content": {
                "application/json": {
                    "example": {"deleted": True, "id": "test_123"}
                }
            }
        },
        404: {
            "description": "Test not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Test with id 'test_123' not found"}
                }
            }
        }
    }
)
async def delete_test(test_id: str, request: Request):
    """
    Delete a test by ID.

    Args:
        test_id: The unique identifier of the test to delete

    Returns:
        Deletion confirmation with the test ID

    Raises:
        HTTPException: 404 if test not found
    """
    success = request.app.state.store.test_repo.delete_by_id(test_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Test with id '{test_id}' not found"
        )

    return {"deleted": True, "id": test_id}
