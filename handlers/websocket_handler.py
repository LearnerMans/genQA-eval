"""
WebSocket handler for real-time progress updates.
"""
import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from services.progress_tracker import (
    progress_tracker,
    WorkflowProgress,
    WorkflowProgressContext,
    ProgressAwareTextExtractionService,
    ProgressAwareChunkingService,
    ProgressAwareEmbeddingService
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])

class ConnectionManager:
    """Manages WebSocket connections for progress updates."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # workflow_id -> connections
        self.test_connections: Dict[str, List[WebSocket]] = {}    # test_id -> connections

    async def connect(self, websocket: WebSocket, workflow_id: str = None, test_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if workflow_id:
            if workflow_id not in self.active_connections:
                self.active_connections[workflow_id] = []
            self.active_connections[workflow_id].append(websocket)

        if test_id:
            if test_id not in self.test_connections:
                self.test_connections[test_id] = []
            self.test_connections[test_id].append(websocket)

        logger.info(f"WebSocket connected - Workflow: {workflow_id}, Test: {test_id}")

    def disconnect(self, websocket: WebSocket, workflow_id: str = None, test_id: str = None):
        """Remove a WebSocket connection."""
        if workflow_id and workflow_id in self.active_connections:
            if websocket in self.active_connections[workflow_id]:
                self.active_connections[workflow_id].remove(websocket)

        if test_id and test_id in self.test_connections:
            if websocket in self.test_connections[test_id]:
                self.test_connections[test_id].remove(websocket)

        logger.info(f"WebSocket disconnected - Workflow: {workflow_id}, Test: {test_id}")

    async def broadcast_to_workflow(self, workflow_id: str, message: dict):
        """Broadcast message to all connections for a specific workflow."""
        if workflow_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[workflow_id].remove(conn)

    async def broadcast_to_test(self, test_id: str, message: dict):
        """Broadcast message to all connections for a specific test."""
        if test_id in self.test_connections:
            disconnected = []
            for connection in self.test_connections[test_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # Remove disconnected connections
            for conn in disconnected:
                self.test_connections[test_id].remove(conn)

# Global connection manager
manager = ConnectionManager()

# Progress callback function
def progress_update_callback(workflow: WorkflowProgress):
    """Callback function for progress updates."""
    asyncio.create_task(_handle_progress_update(workflow))

async def _handle_progress_update(workflow: WorkflowProgress):
    """Handle progress update and broadcast to connected clients."""
    try:
        message = {
            "type": "progress_update",
            "workflow_id": workflow.workflow_id,
            "test_id": workflow.test_id,
            "data": workflow.to_dict()
        }

        # Broadcast to workflow-specific connections
        await manager.broadcast_to_workflow(workflow.workflow_id, message)

        # Broadcast to test-specific connections
        await manager.broadcast_to_test(workflow.test_id, message)

    except Exception as e:
        logger.error(f"Error broadcasting progress update: {str(e)}")

# Register the callback
progress_tracker.add_progress_callback(progress_update_callback)

@router.websocket("/progress/{workflow_id}")
async def websocket_progress_workflow(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time progress updates for a specific workflow.

    Connect to this endpoint to receive live progress updates for a workflow execution.
    """
    await manager.connect(websocket, workflow_id=workflow_id)

    try:
        # Send current progress if workflow exists
        current_progress = progress_tracker.get_workflow_progress(workflow_id)
        if current_progress:
            message = {
                "type": "progress_update",
                "workflow_id": workflow_id,
                "test_id": current_progress.test_id,
                "data": current_progress.to_dict()
            }
            await websocket.send_json(message)

        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()

                # Handle client messages (ping, etc.)
                client_message = json.loads(data)
                if client_message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id=workflow_id)
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {str(e)}")
        manager.disconnect(websocket, workflow_id=workflow_id)

@router.websocket("/progress/test/{test_id}")
async def websocket_progress_test(websocket: WebSocket, test_id: str):
    """
    WebSocket endpoint for real-time progress updates for a specific test.

    Connect to this endpoint to receive live progress updates for all workflows
    associated with a test.
    """
    await manager.connect(websocket, test_id=test_id)

    try:
        # Send current progress for all active workflows of this test
        for workflow_id, workflow in progress_tracker.active_workflows.items():
            if workflow.test_id == test_id:
                message = {
                    "type": "progress_update",
                    "workflow_id": workflow_id,
                    "test_id": test_id,
                    "data": workflow.to_dict()
                }
                await websocket.send_json(message)

        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()

                # Handle client messages (ping, etc.)
                client_message = json.loads(data)
                if client_message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, test_id=test_id)
    except Exception as e:
        logger.error(f"WebSocket error for test {test_id}: {str(e)}")
        manager.disconnect(websocket, test_id=test_id)

@router.get("/progress/{workflow_id}")
async def get_workflow_progress(workflow_id: str):
    """
    HTTP endpoint to get current progress of a workflow.

    This is an alternative to WebSocket for clients that can't use WebSocket connections.
    """
    try:
        progress = progress_tracker.get_workflow_progress(workflow_id)
        if not progress:
            return {"error": "Workflow not found", "workflow_id": workflow_id}

        return progress.to_dict()

    except Exception as e:
        return {"error": str(e), "workflow_id": workflow_id}

@router.get("/progress/test/{test_id}")
async def get_test_progress(test_id: str):
    """
    HTTP endpoint to get current progress of all workflows for a test.
    """
    try:
        workflows = []

        # Get active workflows for this test
        for workflow in progress_tracker.active_workflows.values():
            if workflow.test_id == test_id:
                workflows.append(workflow.to_dict())

        # Get completed workflows for this test
        for workflow in progress_tracker.completed_workflows.values():
            if workflow.test_id == test_id:
                workflows.append(workflow.to_dict())

        return {
            "test_id": test_id,
            "workflows": workflows,
            "count": len(workflows)
        }

    except Exception as e:
        return {"error": str(e), "test_id": test_id}

@router.get("/progress/active")
async def get_all_active_progress():
    """
    Get progress of all currently active workflows.
    """
    try:
        workflows = [
            workflow.to_dict()
            for workflow in progress_tracker.active_workflows.values()
        ]

        return {
            "active_workflows": workflows,
            "count": len(workflows)
        }

    except Exception as e:
        return {"error": str(e)}

# Progress dashboard HTML page
@router.get("/progress/dashboard")
async def progress_dashboard():
    """
    Serve a simple HTML dashboard for monitoring progress.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Evaluation Progress Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .workflow { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
            .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #2196F3); transition: width 0.3s; }
            .step { margin: 5px 0; padding: 5px; background: #f9f9f9; border-radius: 3px; }
            .status-running { color: #2196F3; }
            .status-completed { color: #4CAF50; }
            .status-failed { color: #f44336; }
            .status-pending { color: #ff9800; }
            .metadata { font-size: 0.9em; color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>RAG Evaluation Progress Dashboard</h1>
        <div id="content">
            <p>Loading...</p>
        </div>

        <script>
            const content = document.getElementById('content');

            function formatDuration(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins}:${secs.toString().padStart(2, '0')}`;
            }

            function updateDashboard() {
                fetch('/ws/progress/active')
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            content.innerHTML = `<p>Error: ${data.error}</p>`;
                            return;
                        }

                        let html = `<h2>Active Workflows (${data.count})</h2>`;

                        if (data.active_workflows.length === 0) {
                            html += '<p>No active workflows</p>';
                        } else {
                            data.active_workflows.forEach(workflow => {
                                const progressPercent = workflow.overall_progress.toFixed(1);
                                const duration = formatDuration(workflow.duration);

                                html += `
                                    <div class="workflow">
                                        <h3>Workflow: ${workflow.workflow_id}</h3>
                                        <p><strong>Test:</strong> ${workflow.test_id} | <strong>Status:</strong> ${workflow.status}</p>
                                        <p><strong>Progress:</strong> ${progressPercent}% | <strong>Duration:</strong> ${duration}</p>

                                        <div class="progress-bar">
                                            <div class="progress-fill" style="width: ${progressPercent}%"></div>
                                        </div>

                                        <div style="margin-top: 10px;">
                                            <strong>Steps:</strong>
                                `;

                                Object.entries(workflow.steps).forEach(([stepId, step]) => {
                                    const stepProgress = step.progress_percentage.toFixed(1);
                                    const statusClass = `status-${step.status}`;

                                    html += `
                                        <div class="step">
                                            <strong>${step.name}:</strong> ${stepProgress}% (${step.completed_items}/${step.total_items})
                                            <span class="${statusClass}">(${step.status})</span>
                                            ${step.metadata.current_file ? `<div class="metadata">Current: ${step.metadata.current_file}</div>` : ''}
                                            ${step.metadata.current_url ? `<div class="metadata">Current: ${step.metadata.current_url}</div>` : ''}
                                        </div>
                                    `;
                                });

                                html += '</div></div>';
                            });
                        }

                        content.innerHTML = html;
                    })
                    .catch(error => {
                        content.innerHTML = `<p>Error loading dashboard: ${error}</p>`;
                    });
            }

            // Update every 2 seconds
            setInterval(updateDashboard, 2000);
            updateDashboard(); // Initial load
        </script>
    </body>
    </html>
    """

    return {"html": html_content}

# Enhanced workflow handler with progress tracking
def enhance_workflow_with_progress():
    """Enhance the workflow service with progress tracking."""

    # Store original methods
    original_process = None
    original_update = None

    try:
        from services.workflow_service import WorkflowService

        # Backup original methods
        original_process = WorkflowService.process_test_corpus
        original_update = WorkflowService.update_test_corpus

        async def process_with_progress(self, test_id: str, project_id: str, corpus_id: str,
                                      file_paths=None, urls=None, crawl_depth: int = 1,
                                      embedding_model_name: str = None):
            """Enhanced process_test_corpus with progress tracking."""

            # Define workflow steps
            step_configs = [
                ("extraction", "Text Extraction", (len(file_paths) if file_paths else 0) + (len(urls) if urls else 0)),
                ("chunking", "Content Chunking", 0),  # Will be updated when we know the count
                ("embedding", "Vector Embedding", 0)  # Will be updated when we know the count
            ]

            with WorkflowProgressContext(test_id, project_id, corpus_id, step_configs) as workflow_id:
                # Import here to avoid circular imports
                from services.progress_tracker import (
                    ProgressAwareTextExtractionService,
                    ProgressAwareChunkingService,
                    ProgressAwareEmbeddingService
                )

                # Initialize progress-aware services
                extraction_service = ProgressAwareTextExtractionService(self.extraction_service, progress_tracker)
                chunking_service = ProgressAwareChunkingService(self.chunking_service, progress_tracker)

                # Step 1: Extract text with progress tracking
                extracted_contents = await extraction_service.extract_all_sources(
                    workflow_id, project_id, corpus_id, file_paths, urls, crawl_depth
                )

                if not extracted_contents:
                    return type('WorkflowResult', (), {
                        'success': False,
                        'error_message': 'No content extracted from provided sources',
                        'test_id': test_id,
                        'project_id': project_id,
                        'corpus_id': corpus_id,
                        'collection_name': '',
                        'extraction_summary': {'total_sources': 0, 'files': 0, 'urls': 0, 'total_content_size': 0},
                        'chunking_summary': {'total_chunks': 0},
                        'embedding_summary': {'total_embeddings': 0},
                        'execution_time': 0
                    })()

                # Step 2: Get configuration and chunk content
                config = self.store.config_repo.get_by_test_id(test_id)
                if not config:
                    return type('WorkflowResult', (), {
                        'success': False,
                        'error_message': f'No configuration found for test {test_id}',
                        'test_id': test_id,
                        'project_id': project_id,
                        'corpus_id': corpus_id,
                        'collection_name': '',
                        'extraction_summary': {'total_sources': 0, 'files': 0, 'urls': 0, 'total_content_size': 0},
                        'chunking_summary': {'total_chunks': 0},
                        'embedding_summary': {'total_embeddings': 0},
                        'execution_time': 0
                    })()

                # Update chunking step with actual count
                progress_tracker.update_step(workflow_id, "chunking",
                                           metadata={"total_items": len(extracted_contents)})

                chunks = chunking_service.chunk_extracted_content(workflow_id, extracted_contents, config)

                # Step 3: Create embeddings with progress tracking
                embedding_service = ProgressAwareEmbeddingService(
                    type('EmbeddingService', (), {
                        'generate_embeddings': self.vdb.__class__.generate_embeddings,
                        'create_test_collection': self.vdb.__class__.create_test_collection,
                        'update_test_collection': self.vdb.__class__.update_test_collection
                    })(self.db, self.vdb, embedding_model_name),
                    progress_tracker
                )

                collection_name = await embedding_service.create_test_collection(
                    workflow_id, test_id, chunks, embedding_model_name
                )

                # Return success result (simplified for this example)
                return type('WorkflowResult', (), {
                    'success': True,
                    'test_id': test_id,
                    'project_id': project_id,
                    'corpus_id': corpus_id,
                    'collection_name': collection_name or '',
                    'extraction_summary': {'total_sources': len(extracted_contents), 'files': 0, 'urls': 0, 'total_content_size': 0},
                    'chunking_summary': {'total_chunks': len(chunks)},
                    'embedding_summary': {'total_embeddings': len(chunks)},
                    'execution_time': 0
                })()

        # Replace methods
        WorkflowService.process_test_corpus = process_with_progress

    except Exception as e:
        logger.error(f"Error enhancing workflow with progress: {str(e)}")

# Initialize progress enhancement when module is imported
enhance_workflow_with_progress()
