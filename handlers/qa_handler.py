from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import List
from pydantic import BaseModel, Field
import csv
import io

router = APIRouter(prefix="/qa", tags=["QA"])


class QAResponse(BaseModel):
    """Response model for a QA pair."""
    id: str = Field(..., description="Unique QA pair identifier")
    project_id: str = Field(..., description="The ID of the related project")
    question: str = Field(..., description="The question")
    answer: str = Field(..., description="The answer")
    hash: str = Field(..., description="Hash for duplicate detection")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "qa_123",
                "project_id": "project123",
                "question": "What is RAG?",
                "answer": "RAG stands for Retrieval-Augmented Generation...",
                "hash": "abc123..."
            }
        }


class QACreateRequest(BaseModel):
    """Request model for creating a QA pair."""
    project_id: str = Field(..., description="Project ID", min_length=1)
    question: str = Field(..., description="The question", min_length=1)
    answer: str = Field(..., description="The answer", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project123",
                "question": "What is RAG?",
                "answer": "RAG stands for Retrieval-Augmented Generation, a technique that combines retrieval and generation."
            }
        }


class QABatchCreateResponse(BaseModel):
    """Response model for batch QA creation."""
    created: List[QAResponse] = Field(..., description="Successfully created QA pairs")
    created_count: int = Field(..., description="Number of created QA pairs")
    skipped: List[dict] = Field(..., description="Skipped items (duplicates)")
    skipped_count: int = Field(..., description="Number of skipped items")
    failed: List[dict] = Field(..., description="Failed items with reasons")
    failed_count: int = Field(..., description="Number of failed items")
    total_processed: int = Field(..., description="Total items processed")

    class Config:
        json_schema_extra = {
            "example": {
                "created": [],
                "created_count": 8,
                "skipped": [{"question": "Duplicate?", "reason": "duplicate"}],
                "skipped_count": 2,
                "failed": [],
                "failed_count": 0,
                "total_processed": 10
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
    id: str = Field(..., description="ID of the deleted QA pair")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True,
                "id": "qa_123"
            }
        }


@router.post(
    "",
    response_model=QAResponse,
    status_code=201,
    summary="Create a new QA pair",
    description="Create a new question-answer pair. Duplicates are not allowed.",
    response_description="The created QA pair with generated ID"
)
async def create_qa_pair(qa: QACreateRequest, request: Request):
    """
    Create a new QA pair.

    The QA pair ID is automatically generated.
    Duplicate QA pairs (same question and answer for a project) are rejected.

    Args:
        qa: QA pair creation data with project_id, question, and answer

    Returns:
        The created QA pair with ID and hash

    Raises:
        HTTPException: 400 if duplicate or invalid data
    """
    try:
        created_qa = request.app.state.store.qa_repo.create({
            "project_id": qa.project_id,
            "question": qa.question,
            "answer": qa.answer
        })
        return created_qa
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch",
    response_model=QABatchCreateResponse,
    status_code=201,
    summary="Create multiple QA pairs",
    description="Create multiple QA pairs at once. Duplicates are automatically skipped.",
    response_description="Summary of created, skipped, and failed QA pairs"
)
async def create_qa_pairs_batch(qa_list: List[QACreateRequest], request: Request):
    """
    Create multiple QA pairs in a batch.

    Duplicates are automatically skipped and reported.
    Failed items are reported with reasons.

    Args:
        qa_list: List of QA pairs to create

    Returns:
        Summary with created, skipped, and failed items
    """
    try:
        data_list = [
            {
                "project_id": qa.project_id,
                "question": qa.question,
                "answer": qa.answer
            }
            for qa in qa_list
        ]
        result = request.app.state.store.qa_repo.create_batch(data_list)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upload-csv",
    response_model=QABatchCreateResponse,
    status_code=201,
    summary="Upload QA pairs from CSV",
    description="Upload a CSV file with question-answer pairs. Expected columns: 'question', 'answer'. Duplicates are automatically skipped.",
    response_description="Summary of created, skipped, and failed QA pairs"
)
async def upload_qa_csv(
    request: Request,
    project_id: str = Form(..., description="Project ID"),
    file: UploadFile = File(..., description="CSV file with 'question' and 'answer' columns")
):
    """
    Upload QA pairs from a CSV file.

    The CSV file must have 'question' and 'answer' columns (case-insensitive).
    Duplicates are automatically skipped.

    Args:
        project_id: The project to associate QA pairs with
        file: CSV file with question and answer columns

    Returns:
        Summary with created, skipped, and failed items

    Raises:
        HTTPException: 400 if file format is invalid or processing fails
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read CSV content
        content = await file.read()

        # Handle BOM (Byte Order Mark) for Excel compatibility
        # Try UTF-8 with BOM first, then fall back to UTF-8
        try:
            csv_text = content.decode('utf-8-sig')  # Removes BOM if present
        except UnicodeDecodeError:
            csv_text = content.decode('utf-8')

        csv_file = io.StringIO(csv_text)

        # Parse CSV
        reader = csv.DictReader(csv_file)

        # Normalize headers to lowercase
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")

        # Check for required columns (case-insensitive)
        headers_lower = [h.lower().strip() for h in reader.fieldnames]
        if 'question' not in headers_lower or 'answer' not in headers_lower:
            raise HTTPException(
                status_code=400,
                detail=f"CSV must have 'question' and 'answer' columns. Found: {', '.join(reader.fieldnames)}"
            )

        # Find the actual column names (preserve case)
        question_col = None
        answer_col = None
        for header in reader.fieldnames:
            if header.lower().strip() == 'question':
                question_col = header
            elif header.lower().strip() == 'answer':
                answer_col = header

        # Extract QA pairs
        qa_list = []
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 for header)
            question = row.get(question_col, '').strip()
            answer = row.get(answer_col, '').strip()

            if not question or not answer:
                continue  # Skip empty rows

            qa_list.append({
                "project_id": project_id,
                "question": question,
                "answer": answer
            })

        if not qa_list:
            raise HTTPException(
                status_code=400,
                detail="No valid QA pairs found in CSV. Ensure 'question' and 'answer' columns have data."
            )

        # Create QA pairs in batch
        result = request.app.state.store.qa_repo.create_batch(qa_list)
        return result

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")


@router.get(
    "",
    response_model=List[QAResponse],
    summary="Get all QA pairs",
    description="Retrieve a list of all QA pairs in the system.",
    response_description="List of all QA pairs"
)
async def get_all_qa_pairs(request: Request):
    """
    Retrieve all QA pairs.

    Returns a list of all QA pairs with their IDs, questions, answers, and hashes.
    """
    qa_pairs = request.app.state.store.qa_repo.get_all()
    return qa_pairs


@router.get(
    "/project/{project_id}",
    response_model=List[QAResponse],
    summary="Get QA pairs by project",
    description="Retrieve a list of QA pairs for a specific project.",
    response_description="List of QA pairs scoped to a project"
)
async def get_qa_pairs_by_project(project_id: str, request: Request):
    """
    Retrieve all QA pairs for the given project_id.

    Args:
        project_id: The project identifier to filter QA pairs

    Returns:
        List of QA pairs for the specified project
    """
    qa_pairs = request.app.state.store.qa_repo.get_by_project_id(project_id)
    return qa_pairs


@router.get(
    "/{qa_id}",
    response_model=QAResponse,
    summary="Get a QA pair by ID",
    description="Retrieve a single QA pair by its ID.",
    response_description="The QA pair details"
)
async def get_qa_pair(qa_id: str, request: Request):
    """
    Retrieve a QA pair by ID.

    Args:
        qa_id: The unique identifier of the QA pair

    Returns:
        The QA pair details

    Raises:
        HTTPException: 404 if QA pair not found
    """
    qa_pair = request.app.state.store.qa_repo.get_by_id(qa_id)
    if not qa_pair:
        raise HTTPException(
            status_code=404,
            detail=f"QA pair with id '{qa_id}' not found"
        )
    return qa_pair


@router.delete(
    "/{qa_id}",
    response_model=DeleteResponse,
    summary="Delete a QA pair",
    description="Delete a QA pair by its ID.",
    response_description="Deletion status and QA pair ID"
)
async def delete_qa_pair(qa_id: str, request: Request):
    """
    Delete a QA pair by ID.

    Args:
        qa_id: The unique identifier of the QA pair to delete

    Returns:
        Deletion confirmation with the QA pair ID

    Raises:
        HTTPException: 404 if QA pair not found
    """
    success = request.app.state.store.qa_repo.delete_by_id(qa_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"QA pair with id '{qa_id}' not found"
        )

    return {"deleted": True, "id": qa_id}
