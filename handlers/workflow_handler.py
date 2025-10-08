r"""
FastAPI handlers for the RAG evaluation workflow.
"""
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from db.db import DB
from repos.store import Store
from services.workflow_service import WorkflowService, WorkflowResult
from vectorDb.db import VectorDb

# Request/Response models
class ProcessCorpusRequest(BaseModel):
    """Request model for processing a test corpus."""
    project_id: str = Field(..., description="Project identifier")
    corpus_id: str = Field(..., description="Corpus identifier")
    file_paths: Optional[List[str]] = Field(None, description="List of file paths to process")
    urls: Optional[List[str]] = Field(None, description="List of URLs to process")
    crawl_depth: int = Field(1, description="Web crawling depth", ge=1, le=3)
    embedding_model_name: Optional[str] = Field(None, description="Embedding model to use")

class UpdateCorpusRequest(BaseModel):
    """Request model for updating a test corpus."""
    new_file_paths: Optional[List[str]] = Field(None, description="New file paths to add")
    new_urls: Optional[List[str]] = Field(None, description="New URLs to add")
    crawl_depth: int = Field(1, description="Web crawling depth", ge=1, le=3)

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    test_id: str
    test_name: str
    project_id: str
    corpus_id: Optional[str]
    config: Optional[Dict[str, Any]]
    sources: Dict[str, int]
    chunks: int
    collections: Dict[str, Any]
    status: str

class WorkflowResultResponse(BaseModel):
    """Response model for workflow execution results."""
    test_id: str
    project_id: str
    corpus_id: str
    collection_name: str
    extraction_summary: Dict[str, Any]
    chunking_summary: Dict[str, Any]
    embedding_summary: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None

# Router
router = APIRouter(prefix="/workflow", tags=["Workflow"])

# Dependencies
def get_workflow_service(db: DB = Depends(lambda: None), store: Store = Depends(lambda: None), vdb: VectorDb = Depends(lambda: None)):
    """Dependency to get workflow service instance."""
    if db is None or store is None or vdb is None:
        raise HTTPException(status_code=500, detail="Services not initialized")
    return WorkflowService(db, store, vdb)

@router.post("/process-corpus", response_model=WorkflowResultResponse)
async def process_test_corpus(
    request: ProcessCorpusRequest,
    background_tasks: BackgroundTasks,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Process a complete test corpus through the entire RAG pipeline.

    This endpoint extracts text from files and URLs, chunks the content using
    test-specific configuration, generates embeddings, and creates a vector
    collection for the test.
    """
    try:
        # Run workflow in background for long-running operations
        result = await workflow_service.process_test_corpus(
            test_id="",  # This should be derived from project_id or provided
            project_id=request.project_id,
            corpus_id=request.corpus_id,
            file_paths=request.file_paths,
            urls=request.urls,
            crawl_depth=request.crawl_depth,
            embedding_model_name=request.embedding_model_name
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error_message or "Workflow execution failed"
            )

        return WorkflowResultResponse(**result.__dict__)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/update-corpus", response_model=WorkflowResultResponse)
async def update_test_corpus(
    test_id: str,
    request: UpdateCorpusRequest,
    background_tasks: BackgroundTasks,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Update an existing test corpus with new sources.

    This endpoint adds new files and URLs to an existing test corpus,
    processes them through the pipeline, and updates the vector collection.
    """
    try:
        result = await workflow_service.update_test_corpus(
            test_id=test_id,
            new_file_paths=request.new_file_paths,
            new_urls=request.new_urls,
            crawl_depth=request.crawl_depth
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error_message or "Corpus update failed"
            )

        return WorkflowResultResponse(**result.__dict__)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Corpus update failed: {str(e)}")

@router.get("/status/{test_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    test_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Get the current status of a test's workflow.

    Returns information about the test configuration, sources, chunks,
    and vector collections.
    """
    try:
        status = workflow_service.get_workflow_status(test_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return WorkflowStatusResponse(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.post("/reprocess/{test_id}")
async def reprocess_test_corpus(
    test_id: str,
    background_tasks: BackgroundTasks,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Reprocess an entire test corpus from scratch.

    This endpoint clears existing chunks and collections, then reprocesses
    all corpus items through the complete pipeline.
    """
    try:
        # Get current status to understand what needs to be reprocessed
        status = workflow_service.get_workflow_status(test_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        # TODO: Implement reprocessing logic
        # This would involve:
        # 1. Getting all corpus items for the test
        # 2. Clearing existing chunks and collections
        # 3. Reprocessing through the complete pipeline

        return {
            "message": "Reprocessing started",
            "test_id": test_id,
            "status": "in_progress"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

@router.delete("/collection/{test_id}")
async def delete_test_collection(
    test_id: str,
    collection_name: Optional[str] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Delete vector collections for a specific test.

    Args:
        test_id: Test identifier
        collection_name: Specific collection to delete (optional)
    """
    try:
        from services.embedding_service import EmbeddingService

        embedding_service = EmbeddingService(workflow_service.db, workflow_service.vdb)

        if collection_name:
            # Delete specific collection
            success = embedding_service.delete_collection(collection_name)
            if not success:
                raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        else:
            # Delete all collections for the test
            collections = embedding_service.list_test_collections(test_id)
            deleted_count = 0

            for collection in collections:
                if embedding_service.delete_collection(collection):
                    deleted_count += 1

            if deleted_count == 0:
                raise HTTPException(status_code=404, detail=f"No collections found for test {test_id}")

        return {
            "message": "Collections deleted successfully",
            "test_id": test_id,
            "collections_deleted": deleted_count if not collection_name else 1
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete collections: {str(e)}")

@router.get("/collections/{test_id}")
async def list_test_collections(
    test_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    List all vector collections for a specific test.
    """
    try:
        from services.embedding_service import EmbeddingService

        embedding_service = EmbeddingService(workflow_service.db, workflow_service.vdb)
        collections = embedding_service.list_test_collections(test_id)

        collection_details = {}
        for collection_name in collections:
            info = embedding_service.get_collection_info(collection_name)
            collection_details[collection_name] = info

        return {
            "test_id": test_id,
            "collections": collection_details,
            "count": len(collections)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")

@router.post("/test/{test_id}/search")
async def search_test_collection(
    test_id: str,
    query: str,
    top_k: int = 5,
    collection_name: Optional[str] = None,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    Search for similar content in a test's vector collection.

    Args:
        test_id: Test identifier
        query: Search query text
        top_k: Number of similar chunks to return
        collection_name: Specific collection to search (optional)
    """
    try:
        from services.embedding_service import EmbeddingService

        embedding_service = EmbeddingService(workflow_service.db, workflow_service.vdb)

        # Determine collection name
        if not collection_name:
            # Get default collection for the test
            collections = embedding_service.list_test_collections(test_id)
            if not collections:
                raise HTTPException(status_code=404, detail=f"No collections found for test {test_id}")
            collection_name = collections[0]  # Use first available collection

        # Perform search
        results = embedding_service.search_similar_chunks(
            collection_name=collection_name,
            query=query,
            top_k=top_k
        )

        return {
            "test_id": test_id,
            "collection_name": collection_name,
            "query": query,
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/progress/dashboard")
async def get_progress_dashboard():
    """
    Get an HTML dashboard for monitoring workflow progress.

    Returns a complete HTML page that shows real-time progress updates
    for all active workflows.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Evaluation Progress Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .progress-bar { transition: width 0.5s ease-in-out; }
            .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-800 mb-2">RAG Evaluation Progress Dashboard</h1>
                <p class="text-gray-600">Monitor real-time progress of your RAG evaluation workflows</p>
            </div>

            <!-- Controls -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <div class="flex flex-wrap gap-4 items-center justify-between">
                    <div class="flex items-center gap-4">
                        <button onclick="refreshDashboard()"
                                class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                            🔄 Refresh Now
                        </button>
                        <span class="text-sm text-gray-500" id="lastUpdate">Last updated: Never</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-600">Auto-refresh:</span>
                        <select id="refreshInterval" onchange="changeRefreshInterval()" class="border rounded px-2 py-1 text-sm">
                            <option value="2000">2 seconds</option>
                            <option value="5000" selected>5 seconds</option>
                            <option value="10000">10 seconds</option>
                            <option value="0">Disabled</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Active Workflows -->
            <div id="activeWorkflows" class="space-y-4">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                    <p class="text-center text-gray-600 mt-2">Loading workflows...</p>
                </div>
            </div>

            <!-- WebSocket Connection Status -->
            <div class="mt-8 bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Connection Status</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="text-center">
                        <div id="wsStatus" class="w-4 h-4 rounded-full bg-red-500 mx-auto mb-2"></div>
                        <p class="text-sm text-gray-600">WebSocket: Disconnected</p>
                    </div>
                    <div class="text-center">
                        <div class="w-4 h-4 rounded-full bg-green-500 mx-auto mb-2"></div>
                        <p class="text-sm text-gray-600">API: Connected</p>
                    </div>
                    <div class="text-center">
                        <div id="workflowCount" class="text-2xl font-bold text-blue-600">0</div>
                        <p class="text-sm text-gray-600">Active Workflows</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let refreshInterval = 5000;
            let autoRefreshTimer = null;
            let websocket = null;

            function formatDuration(seconds) {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            }

            function formatFileSize(bytes) {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
            }

            function updateLastUpdate() {
                const now = new Date();
                document.getElementById('lastUpdate').textContent =
                    `Last updated: ${now.toLocaleTimeString()}`;
            }

            function refreshDashboard() {
                fetch('/ws/progress/active')
                    .then(response => response.json())
                    .then(data => {
                        updateLastUpdate();

                        if (data.error) {
                            document.getElementById('activeWorkflows').innerHTML =
                                `<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                                    <p class="text-red-600">Error: ${data.error}</p>
                                </div>`;
                            return;
                        }

                        const container = document.getElementById('activeWorkflows');
                        document.getElementById('workflowCount').textContent = data.count;

                        if (data.active_workflows.length === 0) {
                            container.innerHTML = `
                                <div class="bg-white rounded-lg shadow-md p-8 text-center">
                                    <div class="text-6xl mb-4">📋</div>
                                    <h3 class="text-xl font-semibold text-gray-700 mb-2">No Active Workflows</h3>
                                    <p class="text-gray-500">Start a workflow to see progress updates here</p>
                                </div>
                            `;
                            return;
                        }

                        let html = '';
                        data.active_workflows.forEach(workflow => {
                            const progressPercent = workflow.overall_progress.toFixed(1);
                            const duration = formatDuration(workflow.duration);
                            const statusColor = workflow.status === 'running' ? 'blue' :
                                             workflow.status === 'completed' ? 'green' : 'red';

                            html += `
                                <div class="bg-white rounded-lg shadow-md p-6">
                                    <div class="flex justify-between items-start mb-4">
                                        <div>
                                            <h3 class="text-xl font-semibold text-gray-800">
                                                Test: ${workflow.test_id}
                                            </h3>
                                            <p class="text-gray-600 text-sm">Workflow ID: ${workflow.workflow_id}</p>
                                        </div>
                                        <div class="text-right">
                                            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${statusColor}-100 text-${statusColor}-800">
                                                ${workflow.status.toUpperCase()}
                                            </span>
                                            <p class="text-sm text-gray-500 mt-1">${duration}</p>
                                        </div>
                                    </div>

                                    <!-- Overall Progress -->
                                    <div class="mb-4">
                                        <div class="flex justify-between items-center mb-2">
                                            <span class="text-sm font-medium text-gray-700">Overall Progress</span>
                                            <span class="text-sm text-gray-500">${progressPercent}%</span>
                                        </div>
                                        <div class="w-full bg-gray-200 rounded-full h-3">
                                            <div class="progress-bar bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full"
                                                 style="width: ${progressPercent}%"></div>
                                        </div>
                                    </div>

                                    <!-- Step Details -->
                                    <div class="space-y-3">
                                        <h4 class="font-medium text-gray-700">Steps:</h4>
                            `;

                            Object.entries(workflow.steps).forEach(([stepId, step]) => {
                                const stepProgress = step.progress_percentage.toFixed(1);
                                const stepStatusColor = step.status === 'running' ? 'blue' :
                                                      step.status === 'completed' ? 'green' :
                                                      step.status === 'failed' ? 'red' : 'yellow';

                                html += `
                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex justify-between items-center mb-2">
                                            <div class="flex items-center gap-2">
                                                <span class="font-medium text-gray-800">${step.name}</span>
                                                ${step.status === 'running' ? '<div class="pulse w-2 h-2 bg-blue-500 rounded-full"></div>' : ''}
                                            </div>
                                            <span class="text-sm text-gray-600">
                                                ${stepProgress}% (${step.completed_items}/${step.total_items})
                                            </span>
                                        </div>

                                        <div class="w-full bg-gray-200 rounded-full h-2">
                                            <div class="progress-bar bg-${stepStatusColor}-500 h-2 rounded-full"
                                                 style="width: ${stepProgress}%"></div>
                                        </div>

                                        ${step.metadata.current_file ?
                                            `<p class="text-xs text-gray-500 mt-1">📁 ${step.metadata.current_file}</p>` : ''}
                                        ${step.metadata.current_url ?
                                            `<p class="text-xs text-gray-500 mt-1">🔗 ${step.metadata.current_url}</p>` : ''}
                                        ${step.metadata.batch ?
                                            `<p class="text-xs text-gray-500 mt-1">🔄 Batch ${step.metadata.batch}</p>` : ''}
                                    </div>
                                `;
                            });

                            html += `
                                    </div>

                                    <!-- Metadata -->
                                    <div class="mt-4 pt-4 border-t border-gray-200">
                                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                            <div>
                                                <span class="text-gray-500">Project:</span>
                                                <p class="font-medium">${workflow.project_id}</p>
                                            </div>
                                            <div>
                                                <span class="text-gray-500">Corpus:</span>
                                                <p class="font-medium">${workflow.corpus_id}</p>
                                            </div>
                                            <div>
                                                <span class="text-gray-500">Started:</span>
                                                <p class="font-medium">${new Date(workflow.start_time * 1000).toLocaleTimeString()}</p>
                                            </div>
                                            <div>
                                                <span class="text-gray-500">Current Step:</span>
                                                <p class="font-medium">${workflow.current_step || 'None'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });

                        container.innerHTML = html;
                    })
                    .catch(error => {
                        document.getElementById('activeWorkflows').innerHTML =
                            `<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                                <p class="text-red-600">Error loading dashboard: ${error.message}</p>
                            </div>`;
                    });
            }

            function changeRefreshInterval() {
                const select = document.getElementById('refreshInterval');
                refreshInterval = parseInt(select.value);

                if (autoRefreshTimer) {
                    clearInterval(autoRefreshTimer);
                }

                if (refreshInterval > 0) {
                    autoRefreshTimer = setInterval(refreshDashboard, refreshInterval);
                }
            }

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/progress/active`;

                websocket = new WebSocket(wsUrl);

                websocket.onopen = function() {
                    document.getElementById('wsStatus').className = 'w-4 h-4 rounded-full bg-green-500 mx-auto mb-2';
                    console.log('WebSocket connected');
                };

                websocket.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'progress_update') {
                            refreshDashboard(); // Refresh on progress update
                        }
                    } catch (e) {
                        console.error('Error parsing WebSocket message:', e);
                    }
                };

                websocket.onclose = function() {
                    document.getElementById('wsStatus').className = 'w-4 h-4 rounded-full bg-red-500 mx-auto mb-2';
                    console.log('WebSocket disconnected, reconnecting...');
                    // Reconnect after 5 seconds
                    setTimeout(connectWebSocket, 5000);
                };

                websocket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                refreshDashboard();
                changeRefreshInterval();
                connectWebSocket();
            });

            // Cleanup on page unload
            window.addEventListener('beforeunload', function() {
                if (websocket) {
                    websocket.close();
                }
                if (autoRefreshTimer) {
                    clearInterval(autoRefreshTimer);
                }
            });
        </script>
    </body>
    </html>
    """

    return {"html": html_content}

@router.get("/progress/{workflow_id}/stream")
async def stream_workflow_progress(workflow_id: str):
    """
    Stream progress updates for a specific workflow using Server-Sent Events.

    This endpoint provides real-time progress updates using SSE for clients
    that don't support WebSocket but want live updates.
    """
    from fastapi.responses import StreamingResponse
    import json

    async def generate_progress():
        """Generate progress updates as Server-Sent Events."""
        try:
            from services.progress_tracker import progress_tracker

            # Send initial progress
            progress = progress_tracker.get_workflow_progress(workflow_id)
            if progress:
                yield f"data: {json.dumps(progress.to_dict())}\n\n"

            # Send updates every 2 seconds for 5 minutes
            for _ in range(150):  # 5 minutes * 60 / 2
                await asyncio.sleep(2)

                progress = progress_tracker.get_workflow_progress(workflow_id)
                if progress:
                    yield f"data: {json.dumps(progress.to_dict())}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'not_found'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
