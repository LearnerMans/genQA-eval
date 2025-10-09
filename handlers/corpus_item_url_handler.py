from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/corpus-urls", tags=["Corpus URLs"])

class CorpusItemUrlResponse(BaseModel):
    """Response model for a corpus URL item."""
    id: str = Field(..., description="Unique URL identifier")
    project_id: str = Field(..., description="Project ID this URL belongs to")
    corpus_id: str = Field(..., description="Corpus ID this URL belongs to")
    url: str = Field(..., description="URL address")
    content: str = Field(..., description="Extracted content from the URL")
    created_at: str = Field(..., description="Timestamp when the URL was created")
    extraction_at: Optional[str] = Field(None, description="Timestamp when the content was extracted")
    updated_at: Optional[str] = Field(None, description="Timestamp when the URL was last updated")
    type: str = Field("url", description="Item type")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "url_123",
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "url": "https://example.com",
                "content": "Extracted content from the URL...",
                "created_at": "2024-01-15 10:30:00",
                "extraction_at": "2024-01-15 10:35:00",
                "updated_at": "2024-01-16 14:20:00",
                "type": "url"
            }
        }

class CorpusItemUrlCreateRequest(BaseModel):
    """Request model for creating a corpus URL item."""
    project_id: str = Field(..., description="Project ID to associate the URL with")
    corpus_id: str = Field(..., description="Corpus ID to associate the URL with")
    url: str = Field(..., description="URL address")
    content: str = Field("", description="Content extracted from the URL")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "url": "https://example.com",
                "content": "Content extracted from the URL..."
            }
        }

class CorpusItemUrlUpdateRequest(BaseModel):
    """Request model for updating a corpus URL item."""
    url: Optional[str] = Field(None, description="New URL address")
    content: Optional[str] = Field(None, description="New content extracted from the URL")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://new-example.com",
                "content": "Updated content from the URL..."
            }
        }

class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted URL")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "url_123"
            }
        }

@router.post(
    "",
    response_model=CorpusItemUrlResponse,
    status_code=201,
    summary="Create a new corpus URL item",
    description="Create a new URL item in the corpus.",
    response_description="The created URL item with generated ID and timestamps"
)
async def create_corpus_url(url: CorpusItemUrlCreateRequest, request: Request):
    """
    Create a new corpus URL item.

    Args:
        url: URL creation data

    Returns:
        The created URL item

    Raises:
        HTTPException: 400 if invalid data
    """
    try:
        # If content is empty, try to extract it from the URL
        content = url.content
        if not content.strip():
            try:
                from extractors.extractors import crawl_and_extract_markdown
                content = crawl_and_extract_markdown(url.url, depth=1)
            except Exception as e:
                # If extraction fails, use empty content but log the error
                import logging
                logging.warning(f"Failed to extract content from URL {url.url}: {str(e)}")
                content = ""

        created_url = request.app.state.store.corpus_item_url_repo.create({
            "project_id": url.project_id,
            "corpus_id": url.corpus_id,
            "url": url.url,
            "content": content
        })
        return created_url
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get(
    "/project/{project_id}",
    response_model=List[CorpusItemUrlResponse],
    summary="Get all URLs by project ID",
    description="Retrieve all URL items associated with a specific project.",
    response_description="List of all URL items for the project"
)
async def get_urls_by_project_id(project_id: str, request: Request):
    """
    Get all URLs by project ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        List of all URL items for the project
    """
    urls = request.app.state.store.corpus_item_url_repo.get_by_project_id(project_id)
    return urls

@router.get(
    "/corpus/{corpus_id}",
    response_model=List[CorpusItemUrlResponse],
    summary="Get all URLs by corpus ID",
    description="Retrieve all URL items associated with a specific corpus.",
    response_description="List of all URL items for the corpus"
)
async def get_urls_by_corpus_id(corpus_id: str, request: Request):
    """
    Get all URLs by corpus ID.

    Args:
        corpus_id: The unique identifier of the corpus

    Returns:
        List of all URL items for the corpus
    """
    urls = request.app.state.store.corpus_item_url_repo.get_by_corpus_id(corpus_id)
    return urls

@router.get(
    "/{url_id}",
    response_model=CorpusItemUrlResponse,
    summary="Get URL by ID",
    description="Retrieve a URL item by its unique identifier.",
    response_description="The URL item data"
)
async def get_url_by_id(url_id: str, request: Request):
    """
    Get URL by ID.

    Args:
        url_id: The unique identifier of the URL

    Returns:
        The URL item data

    Raises:
        HTTPException: 404 if URL not found
    """
    url_item = request.app.state.store.corpus_item_url_repo.get_by_id(url_id)

    if not url_item:
        raise HTTPException(
            status_code=404,
            detail=f"URL with id '{url_id}' not found"
        )

    return url_item

@router.put(
    "/{url_id}",
    response_model=CorpusItemUrlResponse,
    summary="Update a URL item",
    description="Update URL item information by its ID.",
    response_description="The updated URL item data"
)
async def update_url(url_id: str, url_update: CorpusItemUrlUpdateRequest, request: Request):
    """
    Update URL by ID.

    Args:
        url_id: The unique identifier of the URL to update
        url_update: The fields to update

    Returns:
        The updated URL item data

    Raises:
        HTTPException: 404 if URL not found
        HTTPException: 400 if no valid fields to update
    """
    try:
        updated_url = request.app.state.store.corpus_item_url_repo.update(url_id, url_update.dict(exclude_unset=True))

        if not updated_url:
            raise HTTPException(
                status_code=404,
                detail=f"URL with id '{url_id}' not found"
            )

        return updated_url
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.put(
    "/{url_id}/content",
    response_model=CorpusItemUrlResponse,
    summary="Update URL content",
    description="Update the extracted content for a URL item.",
    response_description="The updated URL item data"
)
async def update_url_content(url_id: str, content: str, request: Request):
    """
    Update URL content.

    Args:
        url_id: The unique identifier of the URL
        content: The new content to set

    Returns:
        The updated URL item data

    Raises:
        HTTPException: 404 if URL not found
    """
    try:
        # Update content and extraction timestamp
        success = request.app.state.store.corpus_item_url_repo.update_content(url_id, content)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"URL with id '{url_id}' not found"
            )

        # Return updated URL item
        updated_url = request.app.state.store.corpus_item_url_repo.get_by_id(url_id)
        return updated_url
    except Exception as e:
        if "not found" in str(e):
            raise e
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete(
    "/{url_id}",
    response_model=DeleteResponse,
    summary="Delete a URL item",
    description="Delete a URL item by its ID.",
    response_description="Deletion status and URL ID"
)
async def delete_url(url_id: str, request: Request):
    """
    Delete a URL by ID.

    Args:
        url_id: The unique identifier of the URL to delete

    Returns:
        Deletion confirmation with the URL ID

    Raises:
        HTTPException: 404 if URL not found
    """
    success = request.app.state.store.corpus_item_url_repo.delete_by_id(url_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"URL with id '{url_id}' not found"
        )

    return {"deleted": True, "id": url_id}
