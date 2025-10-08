from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/corpus-items", tags=["Corpus Items"])

class CorpusItemResponse(BaseModel):
    """Response model for a corpus item (file or URL)."""
    id: str = Field(..., description="Unique item identifier")
    project_id: str = Field(..., description="Project ID this item belongs to")
    corpus_id: str = Field(..., description="Corpus ID this item belongs to")
    type: str = Field(..., description="Item type: 'file' or 'url'")
    metadata: dict = Field(..., description="Item-specific metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "file_123",
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "type": "file",
                "metadata": {
                    "name": "document.txt",
                    "ext": ".txt",
                    "created_at": "2024-01-15 10:30:00",
                    "extraction_at": "2024-01-15 10:35:00",
                    "updated_at": "2024-01-16 14:20:00"
                }
            }
        }

@router.get(
    "/project/{project_id}",
    response_model=List[CorpusItemResponse],
    summary="Get all corpus items by project ID",
    description="Retrieve all files and URLs associated with a specific project, including type and metadata.",
    response_description="List of all corpus items for the project with type and metadata"
)
async def get_corpus_items_by_project_id(project_id: str, request: Request):
    """
    Get all corpus items (files and URLs) by project ID.

    This endpoint returns a unified view of all corpus items (both files and URLs)
    associated with a project, including their type and relevant metadata.

    Args:
        project_id: The unique identifier of the project

    Returns:
        List of all corpus items for the project with type and metadata

    Raises:
        HTTPException: 404 if project not found or no items found
    """
    try:
        # Get all files for the project
        files = request.app.state.store.corpus_item_file_repo.get_by_project_id(project_id)

        # Get all URLs for the project
        urls = request.app.state.store.corpus_item_url_repo.get_by_project_id(project_id)

        # Combine and format the results
        corpus_items = []

        # Process files
        for file_item in files:
            corpus_items.append({
                "id": file_item["id"],
                "project_id": file_item["project_id"],
                "corpus_id": file_item["corpus_id"],
                "type": file_item["type"],
                "metadata": {
                    "name": file_item["name"],
                    "ext": file_item["ext"],
                    "created_at": file_item["created_at"],
                    "extraction_at": file_item["extraction_at"],
                    "updated_at": file_item["updated_at"]
                }
            })

        # Process URLs
        for url_item in urls:
            corpus_items.append({
                "id": url_item["id"],
                "project_id": url_item["project_id"],
                "corpus_id": url_item["corpus_id"],
                "type": url_item["type"],
                "metadata": {
                    "url": url_item["url"],
                    "created_at": url_item["created_at"],
                    "extraction_at": url_item["extraction_at"],
                    "updated_at": url_item["updated_at"]
                }
            })

        return corpus_items

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get(
    "/corpus/{corpus_id}",
    response_model=List[CorpusItemResponse],
    summary="Get all corpus items by corpus ID",
    description="Retrieve all files and URLs associated with a specific corpus, including type and metadata.",
    response_description="List of all corpus items for the corpus with type and metadata"
)
async def get_corpus_items_by_corpus_id(corpus_id: str, request: Request):
    """
    Get all corpus items (files and URLs) by corpus ID.

    This endpoint returns a unified view of all corpus items (both files and URLs)
    associated with a corpus, including their type and relevant metadata.

    Args:
        corpus_id: The unique identifier of the corpus

    Returns:
        List of all corpus items for the corpus with type and metadata

    Raises:
        HTTPException: 404 if corpus not found or no items found
    """
    try:
        # Get all files for the corpus
        files = request.app.state.store.corpus_item_file_repo.get_by_corpus_id(corpus_id)

        # Get all URLs for the corpus
        urls = request.app.state.store.corpus_item_url_repo.get_by_corpus_id(corpus_id)

        # Combine and format the results
        corpus_items = []

        # Process files
        for file_item in files:
            corpus_items.append({
                "id": file_item["id"],
                "project_id": file_item["project_id"],
                "corpus_id": file_item["corpus_id"],
                "type": file_item["type"],
                "metadata": {
                    "name": file_item["name"],
                    "ext": file_item["ext"],
                    "created_at": file_item["created_at"],
                    "extraction_at": file_item["extraction_at"],
                    "updated_at": file_item["updated_at"]
                }
            })

        # Process URLs
        for url_item in urls:
            corpus_items.append({
                "id": url_item["id"],
                "project_id": url_item["project_id"],
                "corpus_id": url_item["corpus_id"],
                "type": url_item["type"],
                "metadata": {
                    "url": url_item["url"],
                    "created_at": url_item["created_at"],
                    "extraction_at": url_item["extraction_at"],
                    "updated_at": url_item["updated_at"]
                }
            })

        return corpus_items

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
