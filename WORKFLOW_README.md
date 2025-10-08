# RAG Evaluation Workflow System

A comprehensive system for extracting text from files and URLs, chunking content with test-specific configuration, and creating vector collections for RAG evaluation.

## Overview

This system provides a complete pipeline for RAG (Retrieval-Augmented Generation) evaluation:

1. **Text Extraction** - Extract text from various file formats and web URLs while preserving source boundaries
2. **Intelligent Chunking** - Split text into chunks using test-specific configuration (recursive chunking with customizable size and overlap)
3. **Vector Embeddings** - Generate embeddings using OpenAI models and store in test-specific collections
4. **Search & Retrieval** - Search vector collections for similar content
5. **LLM Integration** - Use generative models for question answering with retrieved context

## Architecture

### Core Services

#### TextExtractionService
- **Purpose**: Extract text from files and URLs while preserving boundaries
- **Features**:
  - Support for multiple file formats (PDF, DOCX, Markdown, CSV, Excel)
  - Web crawling with configurable depth
  - Parallel processing for multiple sources
  - Metadata preservation for each source

#### ChunkingService
- **Purpose**: Split extracted text into manageable chunks
- **Features**:
  - Test-specific configuration (chunk size, overlap, strategy)
  - Recursive character-based chunking
  - Metadata tracking for each chunk
  - Database persistence

#### EmbeddingService
- **Purpose**: Generate vector embeddings and manage collections
- **Features**:
  - OpenAI embedding model integration
  - Test-specific vector collections
  - Batch processing for efficiency
  - Similarity search capabilities

#### WorkflowService
- **Purpose**: Orchestrate the complete pipeline
- **Features**:
  - End-to-end workflow execution
  - Error handling and recovery
  - Progress tracking and reporting
  - Update capabilities for existing tests

### Database Schema

The system uses the following database tables:

- **projects** - Top-level organizational unit
- **tests** - Individual evaluation tests
- **corpus** - Document collections for each project
- **config** - Test-specific configuration (chunking, models, etc.)
- **corpus_item_file/url** - Individual source documents
- **sources** - Source metadata and tracking
- **chunks** - Text chunks with source relationships
- **test_runs** - Execution tracking for evaluations

## API Endpoints

### Workflow Management

#### Process Corpus
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

#### Update Corpus
```http
POST /workflow/update-corpus/{test_id}
Content-Type: application/json

{
  "new_file_paths": ["path/to/new-file.pdf"],
  "new_urls": ["https://new-example.com"],
  "crawl_depth": 1
}
```

#### Get Workflow Status
```http
GET /workflow/status/{test_id}
```

#### Reprocess Corpus
```http
POST /workflow/reprocess/{test_id}
```

### Collection Management

#### List Collections
```http
GET /workflow/collections/{test_id}
```

#### Delete Collections
```http
DELETE /workflow/collection/{test_id}
DELETE /workflow/collection/{test_id}?collection_name=specific-collection
```

#### Search Collection
```http
POST /workflow/test/{test_id}/search
Content-Type: application/json

{
  "query": "What is RAG?",
  "top_k": 5,
  "collection_name": "optional-specific-collection"
}
```

## Configuration

### Test Configuration

Each test requires configuration for optimal processing:

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

## Usage Examples

### Basic Workflow

```python
import asyncio
from services.workflow_service import WorkflowService
from db.db import DB
from repos.store import Store
from vectorDb.db import VectorDb

async def run_workflow():
    # Initialize services
    db = DB("data/rag_eval.db")
    store = Store(db)
    vdb = VectorDb("data")

    workflow = WorkflowService(db, store, vdb)

    # Process corpus
    result = await workflow.process_test_corpus(
        test_id="test-123",
        project_id="project-456",
        corpus_id="corpus-789",
        file_paths=["docs/manual.pdf", "docs/guide.md"],
        urls=["https://example.com/docs"],
        crawl_depth=1
    )

    if result.success:
        print(f"✅ Created collection: {result.collection_name}")
        print(f"📊 Processed {result.extraction_summary['total_sources']} sources")
        print(f"✂️ Created {result.chunking_summary['total_chunks']} chunks")
        print(f"🧠 Generated {result.embedding_summary['total_embeddings']} embeddings")

asyncio.run(run_workflow())
```

### Search and Retrieval

```python
from services.embedding_service import EmbeddingService

# Initialize embedding service
embedding_service = EmbeddingService(db, vdb)

# Search for similar content
results = embedding_service.search_similar_chunks(
    collection_name="test_test-123_openai_text_embedding_large_3",
    query="How does RAG work?",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['metadata']['content'][:100]}...")
```

### LLM Integration

```python
from llm import get_llm

# Get relevant chunks
chunks = embedding_service.search_similar_chunks(
    collection_name=collection_name,
    query=question,
    top_k=3
)

# Prepare context for LLM
context = "\n".join([chunk['metadata']['content'] for chunk in chunks])

# Generate answer
llm = get_llm("openai_4o")
messages = [
    {"role": "system", "content": "Answer based on the provided context."},
    {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
]

answer = await llm.generate(messages)
```

## Supported File Formats

### Documents
- **PDF** - Portable Document Format
- **DOCX** - Microsoft Word documents
- **Markdown** - MD and Markdown files

### Data Files
- **CSV** - Comma-separated values (converted to readable text)
- **Excel** - XLSX and XLS files (first sheet by default)

### Web Content
- **HTML Pages** - Web pages with automatic text extraction
- **Crawling** - Configurable depth web crawling

## Best Practices

### Chunking Strategy
- **Small documents** (< 1000 chars): Single chunk per document
- **Large documents**: Use 1000-2000 character chunks with 200-character overlap
- **Code files**: Smaller chunks (500-800 chars) for better granularity
- **Technical docs**: Larger chunks (1500-3000 chars) for context preservation

### Embedding Models
- **General text**: `openai_text_embedding_large_3` (3072 dimensions)
- **Performance**: `openai_text_embedding_small_3` (1536 dimensions)
- **Legacy**: `openai_text_embedding_ada_002` (1536 dimensions)

### Collection Naming
Collections follow the pattern: `test_{test_id}_{embedding_model}`
- Example: `test_abc123_openai_text_embedding_large_3`

## Error Handling

The system includes comprehensive error handling:

- **File not found**: Logged and skipped, processing continues
- **Extraction failures**: Individual source failures don't stop the pipeline
- **API rate limits**: Automatic retry with exponential backoff
- **Database errors**: Transaction rollback with detailed logging

## Performance Considerations

### Batch Processing
- Embeddings are processed in batches of 100 for efficiency
- Large files are chunked before embedding to manage memory
- Parallel processing for multiple sources when possible

### Memory Management
- Large text content is processed in chunks
- Database connections are properly managed and closed
- Vector operations use appropriate indexing for performance

## Monitoring and Debugging

### Logging
All services include structured logging:
- **INFO**: Successful operations and progress
- **WARNING**: Non-critical issues (missing files, etc.)
- **ERROR**: Critical failures with full context

### Status Checking
Use the workflow status endpoint to monitor:
- Source processing progress
- Chunk creation statistics
- Collection information
- Configuration validation

## Integration Examples

### FastAPI Integration
```python
from fastapi import FastAPI
from handlers.workflow_handler import router as workflow_router

app = FastAPI()
app.include_router(workflow_router)

# Now available:
# POST /workflow/process-corpus
# GET /workflow/status/{test_id}
# POST /workflow/test/{test_id}/search
```

### Custom Processing Pipeline
```python
from services import (
    TextExtractionService,
    ChunkingService,
    EmbeddingService
)

# Custom workflow with fine-grained control
extraction_service = TextExtractionService(db, store)
chunking_service = ChunkingService(db, store)
embedding_service = EmbeddingService(db, vdb)

# Process step by step
extracted = await extraction_service.extract_all_sources(...)
chunks = chunking_service.chunk_extracted_content(extracted, config)
collection = await embedding_service.create_test_collection(test_id, chunks)
```

## Troubleshooting

### Common Issues

1. **No content extracted**
   - Check file paths and URLs are accessible
   - Verify file formats are supported
   - Check network connectivity for URLs

2. **Embedding failures**
   - Verify OpenAI API key is set
   - Check API quota and rate limits
   - Ensure embedding model name is correct

3. **Collection not found**
   - Verify test_id is correct
   - Check if workflow completed successfully
   - Confirm embedding model matches configuration

4. **Poor search results**
   - Adjust chunk size for better context
   - Try different embedding models
   - Check if source content is relevant

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Semantic chunking** based on content understanding
- **Multiple embedding model support** (Cohere, Hugging Face, etc.)
- **Advanced search** with filtering and ranking
- **Batch evaluation** for multiple tests
- **Export capabilities** for results and analytics
- **Real-time updates** via WebSocket connections

## Contributing

When extending the system:

1. Follow the existing service pattern (TextExtractionService, ChunkingService, etc.)
2. Add appropriate error handling and logging
3. Update database schema if needed
4. Add tests for new functionality
5. Update this documentation

## License

This RAG evaluation workflow system is part of the larger RAG Eval Core project.
