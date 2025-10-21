from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Response
from typing import List, Optional
from pydantic import BaseModel, Field
import os
from utils.faq_csv_parser import FAQCSVParser, FAQCSVParserError

router = APIRouter(prefix="/corpus-faq", tags=["Corpus FAQ"])

class FAQPairResponse(BaseModel):
    """Response model for a single FAQ pair."""
    id: str = Field(..., description="Unique FAQ pair identifier")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    row_index: int = Field(..., description="Original row index from CSV")

class CorpusItemFAQResponse(BaseModel):
    """Response model for a corpus FAQ item."""
    id: str = Field(..., description="Unique FAQ item identifier")
    project_id: str = Field(..., description="Project ID this FAQ belongs to")
    corpus_id: str = Field(..., description="Corpus ID this FAQ belongs to")
    name: str = Field(..., description="FAQ item name")
    embedding_mode: str = Field(..., description="Embedding mode: 'question_only' or 'both'")
    faq_count: int = Field(..., description="Number of FAQ pairs")
    created_at: str = Field(..., description="Timestamp when the FAQ was created")
    extraction_at: Optional[str] = Field(None, description="Timestamp when the FAQ was extracted")
    updated_at: Optional[str] = Field(None, description="Timestamp when the FAQ was last updated")
    type: str = Field("faq", description="Item type")
    pairs: Optional[List[FAQPairResponse]] = Field(None, description="FAQ pairs (only in detailed view)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "faq_123",
                "project_id": "proj_456",
                "corpus_id": "corpus_789",
                "name": "product_faqs.csv",
                "embedding_mode": "both",
                "faq_count": 25,
                "created_at": "2024-01-15 10:30:00",
                "extraction_at": None,
                "updated_at": None,
                "type": "faq"
            }
        }

class CorpusItemFAQUpdateRequest(BaseModel):
    """Request model for updating a corpus FAQ item."""
    name: Optional[str] = Field(None, description="New FAQ item name")
    embedding_mode: Optional[str] = Field(None, description="New embedding mode: 'question_only' or 'both'")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "updated_faqs.csv",
                "embedding_mode": "question_only"
            }
        }

class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted FAQ item")

class FAQUploadResponse(BaseModel):
    """Response model for FAQ upload with validation results."""
    faq_item: CorpusItemFAQResponse
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors/warnings")
    total_pairs: int = Field(..., description="Total number of FAQ pairs uploaded")
    valid_pairs: int = Field(..., description="Number of valid FAQ pairs")

@router.post(
    "/upload",
    response_model=FAQUploadResponse,
    status_code=201,
    summary="Upload FAQ CSV file to corpus",
    description="Upload a CSV file containing FAQ pairs (question, answer columns) to the corpus."
)
async def upload_faq_to_corpus(
    project_id: str = Form(..., description="Project ID"),
    corpus_id: str = Form(..., description="Corpus ID"),
    embedding_mode: str = Form("both", description="Embedding mode: 'question_only' or 'both'"),
    file: UploadFile = File(..., description="CSV file to upload"),
    request: Request = None
):
    """
    Upload a FAQ CSV file to the corpus.

    Args:
        project_id: Project ID
        corpus_id: Corpus ID
        embedding_mode: How to embed FAQs ('question_only' or 'both')
        file: CSV file to upload (must have 'question' and 'answer' columns)

    Returns:
        The created FAQ item with validation results

    Raises:
        HTTPException: 400 if invalid file or validation errors
    """
    try:
        # Validate embedding mode
        if embedding_mode not in ['question_only', 'both']:
            raise HTTPException(
                status_code=400,
                detail="embedding_mode must be 'question_only' or 'both'"
            )

        # Validate file extension
        filename = file.filename or "unnamed_file.csv"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.csv']:
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported for FAQ upload"
            )

        # Read file content
        content = await file.read()

        # Parse CSV with BOM support
        try:
            faq_pairs, validation_errors = FAQCSVParser.parse(content)
        except FAQCSVParserError as e:
            raise HTTPException(
                status_code=400,
                detail=f"CSV parsing error: {str(e)}"
            )

        # Validate before save
        is_valid, save_errors = FAQCSVParser.validate_before_save(faq_pairs, allow_errors=False)

        if not is_valid:
            all_errors = validation_errors + save_errors
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "FAQ validation failed",
                    "errors": all_errors
                }
            )

        # Filter out pairs with errors
        valid_pairs = [p for p in faq_pairs if not p.get('has_errors', False)]

        # Create FAQ item in database
        created_faq = request.app.state.store.corpus_item_faq_repo.create({
            "project_id": project_id,
            "corpus_id": corpus_id,
            "name": filename,
            "embedding_mode": embedding_mode,
            "pairs": [
                {
                    "question": p["question"],
                    "answer": p["answer"]
                }
                for p in valid_pairs
            ]
        })

        return FAQUploadResponse(
            faq_item=created_faq,
            validation_errors=validation_errors,
            total_pairs=len(faq_pairs),
            valid_pairs=len(valid_pairs)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error uploading FAQ: {str(e)}"
        )

@router.get(
    "/template",
    summary="Download FAQ CSV template",
    description="Download a CSV template file with required headers for FAQ upload.",
    response_description="CSV template file"
)
async def download_faq_template():
    """
    Download FAQ CSV template with required headers.

    Returns:
        CSV file with 'question' and 'answer' headers
    """
    template_content = FAQCSVParser.generate_template()

    return Response(
        content=template_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=faq_template.csv"}
    )

@router.get(
    "/project/{project_id}",
    response_model=List[CorpusItemFAQResponse],
    summary="Get all FAQ items by project ID",
    description="Retrieve all FAQ items associated with a specific project.",
    response_description="List of all FAQ items for the project"
)
async def get_faqs_by_project_id(project_id: str, request: Request):
    """
    Get all FAQ items by project ID.

    Args:
        project_id: The unique identifier of the project

    Returns:
        List of all FAQ items for the project
    """
    faqs = request.app.state.store.corpus_item_faq_repo.get_by_project_id(project_id)
    return faqs

@router.get(
    "/corpus/{corpus_id}",
    response_model=List[CorpusItemFAQResponse],
    summary="Get all FAQ items by corpus ID",
    description="Retrieve all FAQ items associated with a specific corpus.",
    response_description="List of all FAQ items for the corpus"
)
async def get_faqs_by_corpus_id(corpus_id: str, request: Request):
    """
    Get all FAQ items by corpus ID.

    Args:
        corpus_id: The unique identifier of the corpus

    Returns:
        List of all FAQ items for the corpus
    """
    faqs = request.app.state.store.corpus_item_faq_repo.get_by_corpus_id(corpus_id)
    return faqs

@router.get(
    "/{faq_id}",
    response_model=CorpusItemFAQResponse,
    summary="Get FAQ item by ID",
    description="Retrieve a FAQ item by its unique identifier, including all FAQ pairs.",
    response_description="The FAQ item data with pairs"
)
async def get_faq_by_id(faq_id: str, request: Request):
    """
    Get FAQ item by ID.

    Args:
        faq_id: The unique identifier of the FAQ item

    Returns:
        The FAQ item data with all pairs

    Raises:
        HTTPException: 404 if FAQ item not found
    """
    faq_item = request.app.state.store.corpus_item_faq_repo.get_by_id(faq_id)

    if not faq_item:
        raise HTTPException(
            status_code=404,
            detail=f"FAQ item with id '{faq_id}' not found"
        )

    return faq_item

@router.put(
    "/{faq_id}",
    response_model=CorpusItemFAQResponse,
    summary="Update a FAQ item",
    description="Update FAQ item information by its ID.",
    response_description="The updated FAQ item data"
)
async def update_faq(faq_id: str, faq_update: CorpusItemFAQUpdateRequest, request: Request):
    """
    Update FAQ item by ID.

    Args:
        faq_id: The unique identifier of the FAQ item to update
        faq_update: The fields to update

    Returns:
        The updated FAQ item data

    Raises:
        HTTPException: 404 if FAQ item not found
        HTTPException: 400 if invalid update data
    """
    try:
        # Validate embedding_mode if provided
        update_data = faq_update.dict(exclude_unset=True)

        if "embedding_mode" in update_data:
            if update_data["embedding_mode"] not in ['question_only', 'both']:
                raise HTTPException(
                    status_code=400,
                    detail="embedding_mode must be 'question_only' or 'both'"
                )

        updated_faq = request.app.state.store.corpus_item_faq_repo.update(faq_id, update_data)

        if not updated_faq:
            raise HTTPException(
                status_code=404,
                detail=f"FAQ item with id '{faq_id}' not found"
            )

        return updated_faq
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete(
    "/{faq_id}",
    response_model=DeleteResponse,
    summary="Delete a FAQ item",
    description="Delete a FAQ item by its ID (also deletes all associated FAQ pairs).",
    response_description="Deletion status and FAQ item ID"
)
async def delete_faq(faq_id: str, request: Request):
    """
    Delete a FAQ item by ID.

    Args:
        faq_id: The unique identifier of the FAQ item to delete

    Returns:
        Deletion confirmation with the FAQ item ID

    Raises:
        HTTPException: 404 if FAQ item not found
    """
    success = request.app.state.store.corpus_item_faq_repo.delete_by_id(faq_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"FAQ item with id '{faq_id}' not found"
        )

    return {"deleted": True, "id": faq_id}
