# ChunkLab

A comprehensive **RAG (Retrieval-Augmented Generation) Evaluation Platform** with **live progress tracking**, **real-time workflow monitoring**, and **advanced text processing capabilities**.

## 🎯 What This App Does

**ChunkLab** is a complete platform for evaluating how well AI systems can answer questions using retrieved context. It processes documents, creates searchable knowledge bases, runs Q&A tests, and provides detailed performance metrics.

### Core Functionality

1. **📄 Document Processing**: Extract text from PDFs, Word docs, web pages, and other sources
2. **✂️ Intelligent Chunking**: Split documents into optimal-sized pieces for AI processing
3. **🧠 Vector Embeddings**: Create searchable vector databases for semantic similarity
4. **❓ Q&A Testing**: Run automated tests to evaluate AI answer quality
5. **📊 Performance Metrics**: Calculate BLEU, ROUGE, answer relevance, context relevance, and groundedness scores
6. **🔄 Live Monitoring**: Real-time progress tracking with beautiful dashboards
7. **⚖️ Side-by-Side Comparison**: Compare different AI models and configurations
8. **🎨 Modern UI**: React-based interface for easy project management

### Real-World Use Cases

- **Customer Support**: Test how well AI can answer customer questions using company documentation
- **Legal Research**: Evaluate AI performance on legal document Q&A tasks
- **Technical Documentation**: Assess AI understanding of technical manuals and guides
- **Educational Content**: Test AI comprehension of textbooks and learning materials
- **Research Papers**: Evaluate AI performance on academic literature

## 🌟 Key Features

- **🔄 Live Progress Tracking** - Real-time progress updates with WebSocket support
- **📊 Beautiful Dashboard** - Visual progress monitoring with auto-refresh
- **🔧 Advanced Workflow** - Complete text extraction, chunking, and embedding pipeline
- **🎯 Test-Specific Configuration** - Customizable chunking and embedding parameters
- **🌐 Multi-Source Support** - Files (PDF, DOCX, CSV, Excel) and web URLs
- **⚡ High Performance** - Batch processing and parallel operations
- **📈 Comprehensive Monitoring** - Multiple monitoring methods (WebSocket, HTTP, SSE)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Start the Server
```bash
uv run uvicorn main:app --reload
```

### 3. Monitor Progress Dashboard
Visit: **http://localhost:8000/workflow/progress/dashboard**

### 4. Run an Example
```bash
python examples/workflow_example.py
```

## 📋 API Overview

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Progress Dashboard:** http://localhost:8000/workflow/progress/dashboard

## Architecture Pattern

This project follows a layered architecture with clear separation of concerns:

```
           Handlers (API Layer)            ― FastAPI routes, request/response handling
      Repositories (Data Layer)           ― Data access logic, business operations
         Database (Storage)               ― SQLite database connection
```

### Directory Structure

```
 handlers/               # API route handlers
   handlers/__init__.py
   handlers/project_handler.py  # Project endpoints
   handlers/tests_handler.py    # Test endpoints
   handlers/config_handler.py   # Config endpoints
 repos/                  # Repository layer
   repos/__init__.py
   repos/store.py         # Store container & Repository interface
   repos/project_repo.py  # Project repository implementation
   repos/test_repo.py     # Test repository implementation
   repos/config_repo.py   # Config repository implementation
 db/                     # Database layer
   db/__init__.py
   db/db.py               # Database connection & schema
 vectorDb/               # Vector database
   vectorDb/__init__.py
   vectorDb/db.py         # ChromaDB integration
 data/                   # Data storage directory
 main.py                 # FastAPI application entry point
```

## Design Patterns

### 1. Repository Pattern

**Purpose:** Abstracts data access logic from business logic.

**Implementation:**

```python
# repos/store.py
class Repository(ABC):
    """Abstract base class - defines interface"""
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]: pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: pass

    @abstractmethod
    def delete_by_id(self, id: str) -> bool: pass

class Store:
    """Container that holds all repositories"""
    def __init__(self, db: DB):
        self.project_repo = ProjectRepo(db)
        self.test_repo = TestRepo(db)
        self.config_repo = ConfigRepo(db)
```

### 2. Handler Pattern

**Purpose:** Separates API routing and request handling from application logic.

**Implementation:**

```python
# handlers/project_handler.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["Projects"])

class ProjectResponse(BaseModel):
    """Pydantic model for response validation"""
    id: str
    name: str
    created_at: str
    updated_at: str | None

@router.get("", response_model=List[ProjectResponse])
async def get_all_projects(request: Request):
    """Handler accesses repo via request.app.state.store"""
    return request.app.state.store.project_repo.get_all()
```

### 3. Dependency Injection

**Purpose:** Inject dependencies at startup for better testability.

**Implementation:**

```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize dependencies
    app.state.vdb = VectorDb(path=DATA_PATH)
    app.state.db = DB(path=DATA_PATH+"/db.db")
    app.state.store = Store(app.state.db)
    yield
```

## API Documentation

### Base URL

```
http://localhost:8000
```

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints

#### Health Check

```http
GET /
```

**Response:**
```json
{
  "message": "ChunkLab API is running",
  "status": "healthy"
}
```

#### Projects API

##### Create Project

```http
POST /projects
```

**Description:** Create a new project with a unique name.

**Request Body:**
```json
{
  "name": "My RAG Project"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My RAG Project",
  "created_at": "2024-01-15 10:30:00",
  "updated_at": null
}
```

##### Get All Projects

```http
GET /projects
```

**Description:** Retrieve a list of all projects.

**Response:** `200 OK`
```json
[
  {
    "id": "proj_123",
    "name": "My RAG Project",
    "created_at": "2024-01-15 10:30:00",
    "updated_at": "2024-01-16 14:20:00"
  }
]
```

##### Delete Project

```http
DELETE /projects/{project_id}
```

**Description:** Delete a project by its ID (cascades to related data).

**Response:** `200 OK`
```json
{
  "deleted": true,
  "id": "proj_123"
}
```

#### Tests API

##### Create Test

```http
POST /tests
```

**Description:** Create a new test linked to a project.

**Request Body:**
```json
{
  "name": "My Test",
  "project_id": "project123"
}
```

**Response:** `201 Created`
```json
{
  "id": "test_123",
  "name": "My Test",
  "project_id": "project123",
  "created_at": "2024-01-15 10:30:00",
  "updated_at": null
}
```

##### Get All Tests

```http
GET /tests
```

**Description:** Retrieve a list of all tests.

**Response:** `200 OK`
```json
[
  {
    "id": "test_123",
    "name": "My Test",
    "project_id": "project123",
    "created_at": "2024-01-15 10:30:00",
    "updated_at": null
  }
]
```

##### Delete Test

```http
DELETE /tests/{test_id}
```

**Description:** Delete a test by its ID.

**Response:** `200 OK`
```json
{
  "deleted": true,
  "id": "test_123"
}
```

#### Configs API

##### Create Config

```http
POST /configs
```

**Description:** Create or update config for a test (one per test).

**Request Body:**
```json
{
  "test_id": "test_123",
  "type": "semantic",
  "chunk_size": 1000,
  "overlap": 100,
  "generative_model": "openai_4o",
  "embedding_model": "openai_text_embedding_large_3",
  "top_k": 10
}
```

**Response:** `201 Created`
```json
{
  "id": "config_123",
  "test_id": "test_123",
  "type": "semantic",
  "chunk_size": 1000,
  "overlap": 100,
  "generative_model": "openai_4o",
  "embedding_model": "openai_text_embedding_large_3",
  "top_k": 10
}
```

##### Get Config by Test ID

```http
GET /configs/{test_id}
```

**Description:** Retrieve the config for a given test ID.

**Response:** `200 OK` (same as create response)

##### Delete Config by Test ID

```http
DELETE /configs/{test_id}
```

**Description:** Delete the config associated with the test ID.

**Response:** `200 OK`
```json
{
  "deleted": true,
  "test_id": "test_123"
}
```

## Running the Application

### Install Dependencies

```bash
uv sync
```

### Start Server

```bash
uv run uvicorn main:app --reload
```

### Access API

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Database Schema

The application uses SQLite with the following tables:

- **projects**: Core projects
- **tests**: Tests within projects
- **corpus**: Corpus for projects
- **config**: Configurations per test (unique)
- **test_runs**: Execution runs
- **corpus_item_url**: URL sources in corpus
- **corpus_item_file**: File sources in corpus
- **question_answer_pairs**: Q&A data per project
- **evals**: Evaluation results
- **sources**: Source references
- **chunks**: Text chunks
- **eval_chunks**: Evaluation-chunk links

All foreign keys have CASCADE delete.

## Best Practices

1. **Always use Repository pattern** - Never direct DB access from handlers
2. **Use Pydantic models** - Automatic validation
3. **Document endpoints** - Good summaries and descriptions
4. **Handle errors properly** - Appropriate HTTP codes
5. **Access repos via Store** - Consistent pattern

## Future Enhancements

- [ ] Add authentication and authorization
- [ ] Implement pagination for list endpoints
- [ ] Add filtering and sorting capabilities
- [ ] Create repositories for corpus and evaluations
- [ ] Implement logging and monitoring
- [ ] Add API rate limiting
- [ ] Create comprehensive test suite

**Note:** Tests and Config repositories are implemented; docs updated accordingly.

## 🔄 Advanced Workflow System

The system includes a powerful workflow engine for processing text from multiple sources with **live progress tracking**.

### Workflow Features

#### Text Processing Pipeline
1. **Text Extraction** - Extract content from files and URLs while preserving boundaries
2. **Intelligent Chunking** - Split text using test-specific configuration
3. **Vector Embedding** - Generate embeddings and create test-specific collections
4. **Progress Tracking** - Real-time monitoring of all operations

#### Supported File Formats
- **Documents**: PDF, DOCX, Markdown
- **Data Files**: CSV, Excel (XLSX/XLS)
- **Web Content**: HTML pages with configurable crawling depth

### Workflow API Endpoints

#### Process Corpus with Progress Tracking
```http
POST /workflow/process-corpus
Content-Type: application/json

{
  "project_id": "string",
  "corpus_id": "string",
  "file_paths": ["path/to/file1.pdf"],
  "urls": ["https://example.com"],
  "crawl_depth": 1,
  "embedding_model_name": "openai_text_embedding_large_3"
}
```

**Response:**
```json
{
  "test_id": "test_123",
  "project_id": "proj_456",
  "corpus_id": "corp_789",
  "collection_name": "test_test_123_openai_text_embedding_large_3",
  "extraction_summary": {
    "total_sources": 5,
    "files": 2,
    "urls": 3,
    "total_content_size": 50000
  },
  "chunking_summary": {
    "total_chunks": 150,
    "average_size": 850
  },
  "embedding_summary": {
    "total_embeddings": 150,
    "embedding_dimensions": 3072,
    "embedding_model": "openai_text_embedding_large_3"
  },
  "execution_time": 45.2,
  "success": true
}
```

#### Real-Time Progress Monitoring

##### WebSocket Progress Updates
```javascript
// Connect to workflow-specific updates
const ws = new WebSocket('ws://localhost:8000/ws/progress/workflow_123');

// Connect to test-specific updates
const ws = new WebSocket('ws://localhost:8000/ws/progress/test/test_123');

// Handle progress updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress_update') {
    console.log('Progress:', data.data.overall_progress + '%');
  }
};
```

##### HTTP Polling
```http
GET /ws/progress/active
GET /workflow/progress/{workflow_id}
```

##### Server-Sent Events
```javascript
const eventSource = new EventSource('http://localhost:8000/workflow/progress/workflow_123/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.overall_progress + '%');
};
```

#### Beautiful Progress Dashboard
**URL:** `http://localhost:8000/workflow/progress/dashboard`

Features:
- **Real-time progress bars** with smooth animations
- **Step-by-step tracking** showing current operation
- **Visual status indicators** (running, completed, failed)
- **Auto-refresh** with configurable intervals
- **Responsive design** for mobile and desktop
- **Connection status** monitoring

### Configuration Options

#### Test Configuration
```json
{
  "test_id": "unique-test-id",
  "type": "recursive",
  "chunk_size": 1000,
  "overlap": 200,
  "generative_model": "openai_4o",
  "embedding_model": "openai_text_embedding_large_3",
  "top_k": 5
}
```

**Parameters:**
- `type`: Chunking strategy (`recursive` or `semantic`)
- `chunk_size`: Maximum characters per chunk (0-5000)
- `overlap`: Overlap between chunks (0-500)
- `generative_model`: LLM for question answering
- `embedding_model`: Model for vector embeddings
- `top_k`: Default number of similar chunks to retrieve

### Usage Examples

#### Basic Workflow Processing
```python
import asyncio
from services.workflow_service import WorkflowService

async def process_corpus():
    workflow = WorkflowService(db, store, vdb)

    result = await workflow.process_test_corpus(
        test_id="test_123",
        project_id="project_456",
        corpus_id="corpus_789",
        file_paths=["docs/manual.pdf", "docs/guide.md"],
        urls=["https://example.com/docs"],
        crawl_depth=1
    )

    print(f"✅ Created collection: {result.collection_name}")
    print(f"📊 Processed {result.extraction_summary['total_sources']} sources")
    print(f"✂️ Created {result.chunking_summary['total_chunks']} chunks")
    print(f"🧠 Generated {result.embedding_summary['total_embeddings']} embeddings")
```

#### Progress Monitoring
```python
from services.progress_tracker import progress_tracker

def progress_callback(workflow):
    print(f"Progress: {workflow.overall_progress:.1f}%")
    print(f"Status: {workflow.status}")
    if workflow.current_step:
        current = workflow.steps[workflow.current_step]
        print(f"Current: {current.name}")

# Register callback
progress_tracker.add_progress_callback(progress_callback)
```

#### Search Collections
```python
from services.embedding_service import EmbeddingService

embedding_service = EmbeddingService(db, vdb)

# Search for similar content
results = embedding_service.search_similar_chunks(
    collection_name="test_test_123_openai_text_embedding_large_3",
    query="How does RAG work?",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['metadata']['content'][:100]}...")
```

## Progress Tracking System

### Monitoring Methods

#### 1. WebSocket (Real-Time)
- **Endpoint**: `ws://localhost:8000/ws/progress/active`
- **Features**: Instant updates, bidirectional communication
- **Use for**: Real-time dashboards, live monitoring

#### 2. HTTP Polling
- **Endpoint**: `GET /ws/progress/active`
- **Features**: Simple, works with any HTTP client
- **Use for**: Periodic updates, compatibility with older systems

#### 3. Server-Sent Events
- **Endpoint**: `GET /workflow/progress/{workflow_id}/stream`
- **Features**: One-way streaming, automatic reconnection
- **Use for**: Long-running processes, browser-based monitoring

#### 4. Progress Dashboard
- **URL**: `http://localhost:8000/workflow/progress/dashboard`
- **Features**: Beautiful UI, auto-refresh, visual indicators
- **Use for**: Human monitoring, debugging, demonstrations

### Progress Information

Each workflow provides detailed progress information:

```json
{
  "workflow_id": "workflow_1699123456_12345",
  "test_id": "test_123",
  "status": "running",
  "overall_progress": 67.5,
  "duration": 45.2,
  "current_step": "embedding",
  "steps": {
    "extraction": {
      "name": "Text Extraction",
      "progress_percentage": 100.0,
      "status": "completed",
      "total_items": 5,
      "completed_items": 5
    },
    "chunking": {
      "name": "Content Chunking",
      "progress_percentage": 85.0,
      "status": "running",
      "total_items": 150,
      "completed_items": 127
    },
    "embedding": {
      "name": "Vector Embedding",
      "progress_percentage": 0.0,
      "status": "pending",
      "total_items": 150,
      "completed_items": 0
    }
  }
}
```

## Examples and Testing

### Run System Tests
```bash
python test_system.py
```

### Basic Workflow Example
```bash
python examples/workflow_example.py
```

### Progress Tracking Demo
```bash
python examples/progress_example.py
```

### API Testing
```bash
# Health check
curl http://localhost:8000/

# Process corpus
curl -X POST "http://localhost:8000/workflow/process-corpus" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "demo",
    "corpus_id": "demo",
    "urls": ["https://en.wikipedia.org/wiki/RAG"]
  }'
```

## Performance Considerations

### Batch Processing
- **Embedding batches**: 100 chunks per batch for optimal performance
- **Parallel extraction**: Multiple sources processed concurrently
- **Memory management**: Large files processed in chunks

### Monitoring Overhead
- **WebSocket**: Minimal overhead for real-time updates
- **HTTP Polling**: Configurable intervals to balance responsiveness vs. load
- **Progress tracking**: Asynchronous callbacks don't block main processing

### Scalability Features
- **Connection pooling**: Efficient database connection management
- **Batch operations**: Optimized for large document collections
- **Progress streaming**: Real-time updates without memory accumulation
