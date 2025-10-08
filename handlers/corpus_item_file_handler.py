from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Response
from typing import List, Optional
from pydantic import BaseModel, Field
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/corpus-files", tags=["Corpus Files"])

class CorpusItemFileResponse(BaseModel):
    """Response model for a corpus file item."""
    id: str = Field(..., description="Unique file identifier")
    project_id: str = Field(..., description="Project ID this file belongs to")
    corpus_id: str = Field(..., description="Corpus ID this file belongs to")
    name: str = Field(..., description="File name")
    ext: str = Field(..., description="File extension")
    content: str = Field(..., description="File content")
    created_at: str = Field(..., description="Timestamp when the file was created")
    extraction_at: Optional[str] = Field(None, description="Timestamp when the file was extracted")
    updated_at: Optional[str] = Field(None, description="Timestamp when the file was last updated")
    type: str = Field("file", description="Item type")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "file_123",
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "name": "document",
                "ext": ".txt",
                "content": "File content here...",
                "created_at": "2024-01-15 10:30:00",
                "extraction_at": "2024-01-15 10:35:00",
                "updated_at": "2024-01-16 14:20:00",
                "type": "file"
            }
        }

class CorpusItemFileCreateRequest(BaseModel):
    """Request model for creating a corpus file item."""
    project_id: str = Field(..., description="Project ID to associate the file with")
    corpus_id: str = Field(..., description="Corpus ID to associate the file with")
    name: str = Field(..., description="File name")
    ext: str = Field("", description="File extension")
    content: str = Field("", description="File content")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "name": "document",
                "ext": ".txt",
                "content": "File content here..."
            }
        }

class CorpusItemFileUpdateRequest(BaseModel):
    """Request model for updating a corpus file item."""
    name: Optional[str] = Field(None, description="New file name")
    ext: Optional[str] = Field(None, description="New file extension")
    content: Optional[str] = Field(None, description="New file content")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "updated_document",
                "content": "Updated file content..."
            }
        }

class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted file")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "file_123"
            }
        }

@router.post(
    "",
    response_model=CorpusItemFileResponse,
    status_code=201,
    summary="Create a new corpus file item",
    description="Create a new file item in the corpus.",
    response_description="The created file item with generated ID and timestamps"
)
async def create_corpus_file(file: CorpusItemFileCreateRequest, request: Request):
    """
    Create a new corpus file item.

    Args:
        file: File creation data

    Returns:
        The created file item

    Raises:
        HTTPException: 400 if invalid data
    """
    try:
        created_file = request.app.state.store.corpus_item_file_repo.create({
            "project_id": file.project_id,
            "corpus_id": file.corpus_id,
            "name": file.name,
            "ext": file.ext,
            "content": file.content
        })
        return created_file
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post(
    "/upload",
    response_model=CorpusItemFileResponse,
    status_code=201,
    summary="Upload a file to corpus",
    description="Upload a physical file to the corpus."
)
async def upload_file_to_corpus(
    project_id: str = Form(..., description="Project ID"),
    corpus_id: str = Form(..., description="Corpus ID"),
    file: UploadFile = File(..., description="File to upload"),
    request: Request = None
):
    """
    Upload a file to the corpus.

    Args:
        project_id: Project ID
        corpus_id: Corpus ID
        file: File to upload

    Returns:
        The created file item
    """
    try:
        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')

        # Get file extension
        filename = file.filename or "unnamed_file"
        ext = os.path.splitext(filename)[1] if '.' in filename else ""

        created_file = request.app.state.store.corpus_item_file_repo.create({
            "project_id": project_id,
            "corpus_id": corpus_id,
            "name": filename,
            "ext": ext,
            "content": file_content
        })
        return created_file
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get(
    "/project/{project_id}",
    response_model=List[CorpusItemFileResponse],
    summary="Get all files by project ID",
    description="Retrieve all file items associated with a specific project.",
    response_description="List of all file items for the project"
)
async def get_files_by_project_id(project_id: str, request: Request):
    """
    Get all files by project ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        List of all file items for the project
    """
    files = request.app.state.store.corpus_item_file_repo.get_by_project_id(project_id)
    return files

@router.get(
    "/corpus/{corpus_id}",
    response_model=List[CorpusItemFileResponse],
    summary="Get all files by corpus ID",
    description="Retrieve all file items associated with a specific corpus.",
    response_description="List of all file items for the corpus"
)
async def get_files_by_corpus_id(corpus_id: str, request: Request):
    """
    Get all files by corpus ID.

    Args:
        corpus_id: The unique identifier of the corpus

    Returns:
        List of all file items for the corpus
    """
    files = request.app.state.store.corpus_item_file_repo.get_by_corpus_id(corpus_id)
    return files

@router.get(
    "/{file_id}",
    response_model=CorpusItemFileResponse,
    summary="Get file by ID",
    description="Retrieve a file item by its unique identifier.",
    response_description="The file item data"
)
async def get_file_by_id(file_id: str, request: Request):
    """
    Get file by ID.

    Args:
        file_id: The unique identifier of the file

    Returns:
        The file item data

    Raises:
        HTTPException: 404 if file not found
    """
    file_item = request.app.state.store.corpus_item_file_repo.get_by_id(file_id)

    if not file_item:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{file_id}' not found"
        )

    return file_item

@router.put(
    "/{file_id}",
    response_model=CorpusItemFileResponse,
    summary="Update a file item",
    description="Update file item information by its ID.",
    response_description="The updated file item data"
)
async def update_file(file_id: str, file_update: CorpusItemFileUpdateRequest, request: Request):
    """
    Update file by ID.

    Args:
        file_id: The unique identifier of the file to update
        file_update: The fields to update

    Returns:
        The updated file item data

    Raises:
        HTTPException: 404 if file not found
        HTTPException: 400 if no valid fields to update
    """
    try:
        updated_file = request.app.state.store.corpus_item_file_repo.update(file_id, file_update.dict(exclude_unset=True))

        if not updated_file:
            raise HTTPException(
                status_code=404,
                detail=f"File with id '{file_id}' not found"
            )

        return updated_file
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete(
    "/{file_id}",
    response_model=DeleteResponse,
    summary="Delete a file item",
    description="Delete a file item by its ID.",
    response_description="Deletion status and file ID"
)
async def delete_file(file_id: str, request: Request):
    """
    Delete a file by ID.

    Args:
        file_id: The unique identifier of the file to delete

    Returns:
        Deletion confirmation with the file ID

    Raises:
        HTTPException: 404 if file not found
    """
    success = request.app.state.store.corpus_item_file_repo.delete_by_id(file_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{file_id}' not found"
        )

    return {"deleted": True, "id": file_id}

@router.get(
    "/{file_id}/download",
    summary="Download file content",
    description="Download the content of a file item as a text file.",
    response_description="File content as downloadable text"
)
async def download_file(file_id: str, request: Request):
    """
    Download file content.

    Args:
        file_id: The unique identifier of the file

    Returns:
        File content as plain text

    Raises:
        HTTPException: 404 if file not found
    """
    file_item = request.app.state.store.corpus_item_file_repo.get_by_id(file_id)

    if not file_item:
        raise HTTPException(
            status_code=404,
            detail=f"File with id '{file_id}' not found"
        )

    filename = f"{file_item['name']}{file_item['ext']}"
    return Response(
        content=file_item["content"],
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
