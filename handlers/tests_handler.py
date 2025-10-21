from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import List
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tests", tags=["Tests"])


class TestResponse(BaseModel):
    """Response model for a test."""
    id: str = Field(..., description="Unique test identifier")
    project_id: str = Field(...,description="the id of the related project")
    name: str = Field(..., description="Test name")
    training_status: str = Field("not_started", description="Training status of the test")
    created_at: str = Field(..., description="Timestamp when the test was created")
    updated_at: str | None = Field(None, description="Timestamp when the test was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "test_123",
                "project_id":"project123",
                "name": "My Test",
                "training_status": "not_started",
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
                        "training_status": "not_started",
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
                    "example": {"detail": "UNIQUE constraint failed: tests.project_id, tests.name"}
                }
            }
        }
    }
)
async def create_test(test: TestCreateRequest, request: Request):
    """
    Create a new test.

    The test ID and timestamps are automatically generated.
    Test names must be unique within the project.

    Args:
        test: Test creation data with name

    Returns:
        The created test with ID, name, and timestamps

    Raises:
        HTTPException: 400 if test name already exists within the project
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

    Returns a list of all tests with their IDs, names, timestamps and training status.
    """
    tests = request.app.state.store.test_repo.get_all()
    return tests


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Get test by ID",
    description="Retrieve a single test by its ID.",
    response_description="Test details",
    responses={
        200: {
            "description": "Test found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "project_id": "project123",
                        "name": "My Test",
                        "training_status": "completed",
                        "created_at": "2024-01-15 10:30:00",
                        "updated_at": None
                    }
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
async def get_test_by_id(test_id: str, request: Request):
    """
    Retrieve a test by ID.

    Args:
        test_id: The unique identifier of the test

    Returns:
        The test with ID, name, and timestamps

    Raises:
        HTTPException: 404 if test not found
    """
    test = request.app.state.store.test_repo.get_by_id(test_id)

    if not test:
        raise HTTPException(
            status_code=404,
            detail=f"Test with id '{test_id}' not found"
        )

    return test


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

    # Also remove any chunk sources associated with this test (which will cascade-delete chunks)
    try:
        request.app.state.db.execute("DELETE FROM sources WHERE test_id = ?", (test_id,))
    except Exception:
        # Best-effort cleanup; ignore errors
        pass

    # Cascade delete: Delete vector collections associated with this test
    try:
        from services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService(request.app.state.db, request.app.state.vdb)
        test_collections = embedding_service.list_test_collections(test_id)
        for collection_name in test_collections:
            embedding_service.delete_collection(collection_name)
    except Exception as e:
        # Log the error but don't fail the test deletion
        import logging
        logging.error(f"Failed to delete vector collections for test {test_id}: {str(e)}")

    return {"deleted": True, "id": test_id}


class TrainResponse(BaseModel):
    """Response model for starting a training job for a test."""
    test_id: str = Field(..., description="Test identifier")
    workflow_id: str = Field(..., description="Workflow id for progress tracking")
    status: str = Field(..., description="Training job status (started)")


@router.post(
    "/{test_id}/train",
    response_model=TrainResponse,
    summary="Start training for a test",
    description="Create a ChromaDB collection and generate embeddings for the test corpus with progress tracking.",
)
async def train_test(test_id: str, request: Request, background_tasks: BackgroundTasks):
    """
    Kick off training for a test: chunk corpus items, embed chunks, and write to ChromaDB.
    Also updates the test's training_status and exposes progress via `/ws/progress/test/{test_id}`.
    """
    # Validate test exists and gather context
    store = request.app.state.store
    db = request.app.state.db
    vdb = request.app.state.vdb

    test = store.test_repo.get_by_id(test_id) if hasattr(store.test_repo, 'get_by_id') else None
    if not test:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' not found")

    project_id = test["project_id"]

    corpus = store.corpus_repo.get_by_project_id(project_id)
    if not corpus:
        raise HTTPException(status_code=400, detail="No corpus found for this project")

    config = store.config_repo.get_by_test_id(test_id)
    if not config:
        raise HTTPException(status_code=400, detail="Please create a config for this test first")

    # Ensure there are items to process
    files = store.corpus_item_file_repo.get_by_project_id(project_id)
    urls = store.corpus_item_url_repo.get_by_project_id(project_id)
    faqs = store.corpus_item_faq_repo.get_by_project_id(project_id)
    if (len(files) + len(urls) + len(faqs)) == 0:
        raise HTTPException(status_code=400, detail="Add files, URLs, or FAQs to the corpus before training")

    # Validate environment prerequisites early (e.g., OpenAI key if required)
    import os
    embedding_model_name = config.get('embedding_model', 'openai_text_embedding_large_3')
    if embedding_model_name.startswith('openai_') and not os.environ.get('OPENAI_API_KEY'):
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not set for selected embedding model")

    # Update training status to in_progress
    store.test_repo.update_training_status(test_id, "in_progress")

    # Build and launch background task
    from services.progress_tracker import progress_tracker, WorkflowProgressContext
    from services.chunking_service import ChunkingService
    from services.text_extraction_service import ExtractedContent
    from llm import get_embedding_model
    import uuid
    import time
    from datetime import datetime

    async def run_training():
        # Count FAQ pairs for progress tracking
        total_faq_pairs = sum(faq.get('faq_count', 0) for faq in faqs)

        step_configs = [
            ("extraction", "Text Extraction", len(files) + len(urls) + total_faq_pairs),
            ("chunking", "Content Chunking", 0),
            ("embedding", "Vector Embedding", 0),
        ]

        workflow_id = None
        try:
            # Assign a workflow id and record steps
            with WorkflowProgressContext(test_id, project_id, corpus["id"], step_configs) as wf_id:
                workflow_id_local = wf_id

                # Step 1: Simulated extraction from stored corpus items (we already have content)
                progress_tracker.start_step(workflow_id_local, "extraction")
                extracted_contents = []

                for idx, f in enumerate(files):
                    # Create a source row so chunks can reference it
                    source_id = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO sources (id, type, path_or_link, test_id) VALUES (?, ?, ?, ?)",
                        (source_id, 'file', f["name"], test_id)  # match by filename for status queries
                    )
                    extracted_contents.append(
                        ExtractedContent(
                            source_id=source_id,
                            source_type='file',
                            source_path=f["name"],
                            content=f.get("content", ""),
                            extracted_at=datetime.now().isoformat(),
                            metadata={
                                'file_name': f["name"],
                                'file_extension': f.get("ext", "").lstrip('.'),
                                'file_size': len(f.get("content", "")),
                                'corpus_item_id': f["id"],
                            },
                        )
                    )
                    progress_tracker.update_step(workflow_id_local, "extraction", completed_items=idx + 1)

                start_idx = len(files)
                for jdx, u in enumerate(urls):
                    source_id = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO sources (id, type, path_or_link, test_id) VALUES (?, ?, ?, ?)",
                        (source_id, 'url', u["url"], test_id)  # exact URL for joins
                    )
                    extracted_contents.append(
                        ExtractedContent(
                            source_id=source_id,
                            source_type='url',
                            source_path=u["url"],
                            content=u.get("content", ""),
                            extracted_at=datetime.now().isoformat(),
                            metadata={
                                'url': u["url"],
                                'content_size': len(u.get("content", "")),
                                'corpus_item_id': u["id"],
                            },
                        )
                    )
                    progress_tracker.update_step(
                        workflow_id_local, "extraction", completed_items=start_idx + jdx + 1
                    )

                # Process FAQ items
                faq_start_idx = len(files) + len(urls)
                faq_progress = 0
                for faq_item in faqs:
                    # Get FAQ pairs for this item
                    pairs = store.corpus_item_faq_repo.get_faq_pairs(faq_item["id"])
                    embedding_mode = faq_item.get("embedding_mode", "both")

                    # Create source for FAQ item
                    source_id = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO sources (id, type, path_or_link, test_id) VALUES (?, ?, ?, ?)",
                        (source_id, 'faq', faq_item["id"], test_id)
                    )

                    # Each FAQ pair becomes an ExtractedContent
                    for pair in pairs:
                        question = pair["question"]
                        answer = pair["answer"]

                        # Determine embedding text based on mode
                        if embedding_mode == 'question_only':
                            embedding_text = question
                        else:  # 'both'
                            embedding_text = f"Q: {question}\nA: {answer}"

                        extracted_contents.append(
                            ExtractedContent(
                                source_id=source_id,
                                source_type='faq',
                                source_path=faq_item["id"],
                                content=f"Q: {question}\nA: {answer}",  # Content is always question + answer
                                extracted_at=datetime.now().isoformat(),
                                metadata={
                                    'faq_item_id': faq_item["id"],
                                    'faq_pair_id': pair["id"],
                                    'question': question,
                                    'answer': answer,
                                    'embedding_mode': embedding_mode,
                                    'embedding_text': embedding_text,
                                    'row_index': pair.get("row_index", 0)
                                },
                            )
                        )
                        faq_progress += 1
                        progress_tracker.update_step(
                            workflow_id_local, "extraction", completed_items=faq_start_idx + faq_progress
                        )

                progress_tracker.update_step(workflow_id_local, "extraction", status="completed")

                # Step 2: Chunking with per-item progress
                from services.progress_tracker import ProgressAwareChunkingService
                chunking_service = ChunkingService(db, store)
                p_chunk = ProgressAwareChunkingService(chunking_service, progress_tracker)

                progress_tracker.update_step(
                    workflow_id_local, "chunking", total_items=len(extracted_contents)
                )
                chunks = p_chunk.chunk_extracted_content(workflow_id_local, extracted_contents, config)

                # Step 3: Embedding with batch progress
                embedding_model_name = config.get('embedding_model', 'openai_text_embedding_large_3')
                collection_name = f"test_{test_id}_{embedding_model_name}"

                # If collection exists, delete to retrain
                try:
                    existing = vdb.list_collections()
                    if collection_name in existing:
                        vdb.delete_collection(collection_name)
                except Exception:
                    pass

                # Create collection
                vdb.create_collection(collection_name)

                # Prepare embedding model
                model = get_embedding_model(embedding_model_name)

                total = len(chunks)
                progress_tracker.update_step(
                    workflow_id_local, "embedding", total_items=total
                )

                batch_size = 100
                added = 0
                for i in range(0, total, batch_size):
                    batch = chunks[i:i + batch_size]
                    # For FAQ chunks, use embedding_text from metadata; otherwise use content
                    texts = []
                    for c in batch:
                        if c.source_type == 'faq' and 'embedding_text' in c.metadata:
                            texts.append(c.metadata['embedding_text'])
                        else:
                            texts.append(c.content)

                    vectors = await model.embed_texts(texts)

                    payload = []
                    for c, vec in zip(batch, vectors):
                        metadata_dict = {
                            'test_id': test_id,
                            'source_id': c.source_id,
                            'content': c.content,
                            'chunk_index': c.chunk_index,
                            'source_type': c.source_type,
                            'embedding_model': embedding_model_name,
                        }

                        # Add FAQ-specific metadata if present
                        if c.source_type == 'faq':
                            metadata_dict['question'] = c.metadata.get('question', '')
                            metadata_dict['embedding_mode'] = c.metadata.get('embedding_mode', 'both')

                        payload.append({
                            'id': c.chunk_id,
                            'vector': vec,
                            'metadata': metadata_dict
                        })

                    vdb.add_to_collection(collection_name, payload)
                    added += len(batch)
                    progress_tracker.update_step(
                        workflow_id_local, "embedding", completed_items=added,
                        metadata={"batch": f"{(i//batch_size)+1}", "batch_progress": f"{added}/{total}"}
                    )

                progress_tracker.update_step(workflow_id_local, "embedding", status="completed")

                # Mark test as trained
                store.test_repo.update_training_status(test_id, "completed")

                return workflow_id_local
        except Exception as e:
            # Mark test as failed
            try:
                store.test_repo.update_training_status(test_id, "failed")
            except Exception:
                pass
            raise e

    # Launch and get a workflow id by creating a temporary context to allocate id
    # We create a throwaway context to obtain workflow_id synchronously for the response
    wf_id = request.app.state.store.test_repo.get_by_id(test_id)["id"] + f"_{int(time.time())}"

    # Properly start the async task
    # We call run_training and it will create the Progress context internally and manage updates
    import asyncio
    asyncio.create_task(run_training())

    return TrainResponse(test_id=test_id, workflow_id=wf_id, status="started")
