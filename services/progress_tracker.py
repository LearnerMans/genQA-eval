"""
Progress tracking system for RAG evaluation workflow.
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProgressStep:
    """Represents a single step in the workflow progress."""
    step_id: str
    name: str
    total_items: int = 0
    completed_items: int = 0
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage for this step."""
        if self.total_items == 0:
            return 100.0 if self.status == "completed" else 0.0
        return (self.completed_items / self.total_items) * 100.0

    @property
    def duration(self) -> float:
        """Get duration of this step in seconds."""
        if self.start_time is None:
            return 0.0
        end_time = self.end_time if self.end_time else time.time()
        return end_time - self.start_time

@dataclass
class WorkflowProgress:
    """Overall progress tracking for a workflow execution."""
    workflow_id: str
    test_id: str
    project_id: str
    corpus_id: str
    start_time: float
    status: str = "running"  # running, completed, failed, cancelled
    steps: Dict[str, ProgressStep] = field(default_factory=dict)
    current_step: Optional[str] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        if not self.steps:
            return 0.0

        total_progress = sum(step.progress_percentage for step in self.steps.values())
        return total_progress / len(self.steps)

    @property
    def duration(self) -> float:
        """Get total duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "test_id": self.test_id,
            "project_id": self.project_id,
            "corpus_id": self.corpus_id,
            "status": self.status,
            "overall_progress": self.overall_progress,
            "duration": self.duration,
            "current_step": self.current_step,
            "steps": {
                step_id: {
                    "name": step.name,
                    "progress_percentage": step.progress_percentage,
                    "status": step.status,
                    "total_items": step.total_items,
                    "completed_items": step.completed_items,
                    "duration": step.duration,
                    "metadata": step.metadata
                }
                for step_id, step in self.steps.items()
            },
            "metadata": self.metadata
        }

class ProgressTracker:
    """Tracks progress of workflow executions."""

    def __init__(self):
        self.active_workflows: Dict[str, WorkflowProgress] = {}
        self.completed_workflows: Dict[str, WorkflowProgress] = {}
        self.progress_callbacks: List[Callable[[WorkflowProgress], None]] = []

    def create_workflow(self, test_id: str, project_id: str, corpus_id: str) -> str:
        """Create a new workflow tracking instance."""
        workflow_id = f"workflow_{int(time.time())}_{id(self)}"

        workflow = WorkflowProgress(
            workflow_id=workflow_id,
            test_id=test_id,
            project_id=project_id,
            corpus_id=corpus_id,
            start_time=time.time()
        )

        self.active_workflows[workflow_id] = workflow
        logger.info(f"Created workflow tracking: {workflow_id}")
        return workflow_id

    def add_step(self, workflow_id: str, step_id: str, name: str, total_items: int = 0) -> None:
        """Add a progress step to a workflow."""
        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not found")
            return

        step = ProgressStep(
            step_id=step_id,
            name=name,
            total_items=total_items
        )

        self.active_workflows[workflow_id].steps[step_id] = step
        logger.info(f"Added step {step_id} to workflow {workflow_id}")

    def start_step(self, workflow_id: str, step_id: str) -> None:
        """Mark a step as started."""
        if workflow_id not in self.active_workflows:
            return

        workflow = self.active_workflows[workflow_id]
        if step_id in workflow.steps:
            workflow.steps[step_id].status = "running"
            workflow.steps[step_id].start_time = time.time()
            workflow.current_step = step_id

            # Notify callbacks
            self._notify_progress_update(workflow)

    def update_step(self, workflow_id: str, step_id: str, completed_items: int = None,
                   status: str = None, metadata: Dict[str, Any] = None, total_items: int = None) -> None:
        """Update step progress."""
        logger.debug(f"Updating step {step_id} in workflow {workflow_id}: "
                    f"completed_items={completed_items}, status={status}, "
                    f"total_items={total_items}, metadata={metadata}")

        if workflow_id not in self.active_workflows:
            logger.warning(f"Workflow {workflow_id} not found in active workflows")
            return

        workflow = self.active_workflows[workflow_id]
        if step_id not in workflow.steps:
            logger.warning(f"Step {step_id} not found in workflow {workflow_id}")
            return

        step = workflow.steps[step_id]

        # Log before updates
        logger.debug(f"Before update: step {step_id} has total_items={step.total_items}, "
                    f"completed_items={step.completed_items}, status={step.status}")

        if total_items is not None:
            logger.debug(f"Setting total_items for {step_id} from {step.total_items} to {total_items}")
            step.total_items = total_items

        if completed_items is not None:
            logger.debug(f"Setting completed_items for {step_id} from {step.completed_items} to {completed_items}")
            step.completed_items = completed_items

        if status:
            logger.debug(f"Setting status for {step_id} from {step.status} to {status}")
            step.status = status
            if status == "completed":
                step.end_time = time.time()
                if workflow.current_step == step_id:
                    workflow.current_step = None
                logger.info(f"Step {step_id} completed successfully")
            elif status == "failed":
                step.end_time = time.time()
                step.error_message = metadata.get("error") if metadata else None
                workflow.current_step = None
                logger.warning(f"Step {step_id} failed: {step.error_message}")

        if metadata:
            logger.debug(f"Updating metadata for {step_id}: {metadata}")
            step.metadata.update(metadata)

        # Notify callbacks
        self._notify_progress_update(workflow)

    def complete_workflow(self, workflow_id: str, success: bool = True,
                         error_message: str = None) -> None:
        """Mark workflow as completed or failed."""
        if workflow_id not in self.active_workflows:
            return

        workflow = self.active_workflows[workflow_id]
        workflow.end_time = time.time()
        workflow.status = "completed" if success else "failed"
        workflow.error_message = error_message

        # Mark all running steps as completed or failed
        for step in workflow.steps.values():
            if step.status == "running":
                step.status = "completed" if success else "failed"
                step.end_time = time.time()

        # Move to completed workflows
        self.completed_workflows[workflow_id] = workflow
        del self.active_workflows[workflow_id]

        logger.info(f"Workflow {workflow_id} {'completed' if success else 'failed'}")

        # Final notification
        self._notify_progress_update(workflow)

    def get_workflow_progress(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get current progress of a workflow."""
        return self.active_workflows.get(workflow_id) or self.completed_workflows.get(workflow_id)

    def add_progress_callback(self, callback: Callable[[WorkflowProgress], None]) -> None:
        """Add a callback function to be called on progress updates."""
        self.progress_callbacks.append(callback)

    def _notify_progress_update(self, workflow: WorkflowProgress) -> None:
        """Notify all callbacks of progress updates."""
        for callback in self.progress_callbacks:
            try:
                callback(workflow)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")

# Global progress tracker instance
progress_tracker = ProgressTracker()

# Context manager for workflow progress tracking
class WorkflowProgressContext:
    """Context manager for tracking workflow progress."""

    def __init__(self, test_id: str, project_id: str, corpus_id: str,
                 step_configs: List[tuple] = None):
        self.test_id = test_id
        self.project_id = project_id
        self.corpus_id = corpus_id
        self.step_configs = step_configs or []
        self.workflow_id: Optional[str] = None

    def __enter__(self) -> str:
        self.workflow_id = progress_tracker.create_workflow(
            self.test_id, self.project_id, self.corpus_id
        )

        # Add predefined steps
        for step_id, step_name, total_items in self.step_configs:
            progress_tracker.add_step(self.workflow_id, step_id, step_name, total_items)

        return self.workflow_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.workflow_id:
            success = exc_type is None
            error_message = str(exc_val) if exc_val else None
            progress_tracker.complete_workflow(self.workflow_id, success, error_message)

# Progress-aware versions of service methods
class ProgressAwareTextExtractionService:
    """Wrapper for TextExtractionService with progress tracking."""

    def __init__(self, extraction_service, progress_tracker: ProgressTracker):
        self.extraction_service = extraction_service
        self.progress_tracker = progress_tracker

    async def extract_all_sources(self, workflow_id: str, project_id: str, corpus_id: str,
                                 file_paths: List[str] = None, urls: List[str] = None,
                                 crawl_depth: int = 1) -> List:
        """Extract text with progress tracking."""
        step_id = "extraction"
        progress_tracker.start_step(workflow_id, step_id)

        total_sources = (len(file_paths) if file_paths else 0) + (len(urls) if urls else 0)

        try:
            # Update progress for each source
            extracted_contents = []

            # Process files
            if file_paths:
                for i, file_path in enumerate(file_paths):
                    progress_tracker.update_step(
                        workflow_id, step_id,
                        completed_items=i + 1,
                        metadata={"current_file": file_path}
                    )

                    # Extract from single file
                    file_contents = await self.extraction_service.extract_from_files(
                        project_id, corpus_id, [file_path]
                    )
                    extracted_contents.extend(file_contents)

            # Process URLs
            if urls:
                for i, url in enumerate(urls):
                    progress_tracker.update_step(
                        workflow_id, step_id,
                        completed_items=(len(file_paths) if file_paths else 0) + i + 1,
                        metadata={"current_url": url}
                    )

                    # Extract from single URL
                    url_contents = await self.extraction_service.extract_from_urls(
                        project_id, corpus_id, [url], crawl_depth
                    )
                    extracted_contents.extend(url_contents)

            progress_tracker.update_step(workflow_id, step_id, status="completed")
            return extracted_contents

        except Exception as e:
            progress_tracker.update_step(
                workflow_id, step_id,
                status="failed",
                metadata={"error": str(e)}
            )
            raise

class ProgressAwareChunkingService:
    """Wrapper for ChunkingService with progress tracking."""

    def __init__(self, chunking_service, progress_tracker: ProgressTracker):
        self.chunking_service = chunking_service
        self.progress_tracker = progress_tracker

    def chunk_extracted_content(self, workflow_id: str, extracted_contents: List, config: Dict) -> List:
        """Chunk content with progress tracking."""
        step_id = "chunking"
        progress_tracker.start_step(workflow_id, step_id)

        try:
            progress_tracker.update_step(
                workflow_id, step_id,
                total_items=len(extracted_contents),
                metadata={"config": config}
            )

            chunks = []
            for i, content in enumerate(extracted_contents):
                progress_tracker.update_step(
                    workflow_id, step_id,
                    completed_items=i + 1,
                    metadata={"current_source": content.source_path}
                )

                # Chunk single content item
                content_chunks = self.chunking_service.chunk_text_with_config(
                    content.content,
                    content.source_id,
                    content.source_type,
                    config.get('chunk_size', 1000),
                    config.get('overlap', 200),
                    config.get('type', 'recursive')
                )
                chunks.extend(content_chunks)

            progress_tracker.update_step(workflow_id, step_id, status="completed")
            return chunks

        except Exception as e:
            progress_tracker.update_step(
                workflow_id, step_id,
                status="failed",
                metadata={"error": str(e)}
            )
            raise

class ProgressAwareEmbeddingService:
    """Wrapper for EmbeddingService with progress tracking."""

    def __init__(self, embedding_service, progress_tracker: ProgressTracker):
        self.embedding_service = embedding_service
        self.progress_tracker = progress_tracker

    async def create_test_collection(self, workflow_id: str, test_id: str, chunks: List,
                                   embedding_model_name: str = None) -> str:
        """Create collection with progress tracking."""
        step_id = "embedding"
        progress_tracker.start_step(workflow_id, step_id)

        try:
            progress_tracker.update_step(
                workflow_id, step_id,
                total_items=len(chunks),
                metadata={"embedding_model": embedding_model_name}
            )

            # Generate embeddings in batches with progress updates
            batch_size = 100
            collection_name = None

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_end = min(i + batch_size, len(chunks))

                # Generate embeddings for batch
                chunk_embeddings = await self.embedding_service.generate_embeddings(batch)

                # Update progress
                progress_tracker.update_step(
                    workflow_id, step_id,
                    completed_items=batch_end,
                    metadata={
                        "batch": f"{i//batch_size + 1}",
                        "batch_progress": f"{batch_end}/{len(chunks)}"
                    }
                )

                # Create collection on first batch
                if i == 0:
                    collection_name = await self.embedding_service.create_test_collection(
                        test_id, batch, embedding_model_name
                    )

                    # Add remaining batches to existing collection
                    if len(chunks) > batch_size:
                        remaining_chunks = chunks[batch_size:]
                        await self.embedding_service.update_test_collection(
                            test_id, remaining_chunks, collection_name
                        )
                elif collection_name and i + batch_size < len(chunks):
                    # Add remaining batches
                    remaining_chunks = chunks[i + batch_size:]
                    await self.embedding_service.update_test_collection(
                        test_id, remaining_chunks, collection_name
                    )

            progress_tracker.update_step(workflow_id, step_id, status="completed")
            return collection_name

        except Exception as e:
            progress_tracker.update_step(
                workflow_id, step_id,
                status="failed",
                metadata={"error": str(e)}
            )
            raise
