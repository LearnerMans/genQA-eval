# 🚀 Getting Started with RAG Eval Core

A comprehensive guide to using the RAG evaluation workflow system with live progress tracking.

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key (for LLM and embedding features)
- Basic understanding of REST APIs
- Familiarity with WebSocket connections (optional, for real-time updates)

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required for LLM and embedding features
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional: Configure data directory
export RAG_EVAL_DATA_DIR="./data"
```

### 3. Start the Server

```bash
# Development mode with auto-reload
uv run uvicorn main:app --reload

# Production mode
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Run system tests
python test_system.py

# Expected output: "🎉 All tests passed! System is ready to use."
```

## 🎯 Your First Workflow

Let's create a complete RAG evaluation workflow from start to finish.

### Step 1: Set Up Project Structure

```python
import asyncio
from db.db import DB
from repos.store import Store

# Initialize database and repositories
db = DB("data/rag_eval.db")
store = Store(db)

# Create a project
project = store.project_repo.create({"name": "My First RAG Project"})
print(f"✅ Created project: {project['name']}")

# Create a corpus for documents
corpus = store.corpus_repo.create({
    "project_id": project["id"],
    "name": "Sample Documents"
})

# Create a test configuration
test = store.test_repo.create({
    "project_id": project["id"],
    "name": "Document QA Test"
})

# Configure chunking and embedding parameters
config = store.config_repo.create({
    "test_id": test["id"],
    "type": "recursive",
    "chunk_size": 1000,
    "overlap": 200,
    "generative_model": "openai_4o",
    "embedding_model": "openai_text_embedding_large_3",
    "top_k": 5
})

print(f"✅ Created test: {test['name']}")
```

### Step 2: Process Documents

```python
from services.workflow_service import WorkflowService
from vectorDb.db import VectorDb

# Initialize services
vdb = VectorDb("data")
workflow_service = WorkflowService(db, store, vdb)

# Process corpus with sample content
result = await workflow_service.process_test_corpus(
    test_id=test["id"],
    project_id=project["id"],
    corpus_id=corpus["id"],
    file_paths=[],  # Add your file paths here
    urls=[
        "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        "https://en.wikipedia.org/wiki/Vector_database"
    ],
    crawl_depth=1,
    embedding_model_name="openai_text_embedding_large_3"
)

if result.success:
    print("🎉 Workflow completed successfully!")
    print(f"📊 Collection: {result.collection_name}")
    print(f"📄 Sources processed: {result.extraction_summary['total_sources']}")
    print(f"✂️ Chunks created: {result.chunking_summary['total_chunks']}")
    print(f"🧠 Embeddings generated: {result.embedding_summary['total_embeddings']}")
else:
    print(f"❌ Workflow failed: {result.error_message}")
```

### Step 3: Monitor Progress in Real-Time

#### Option A: Beautiful Web Dashboard
Visit: **http://localhost:8000/workflow/progress/dashboard**

#### Option B: WebSocket Connection
```javascript
// Connect to real-time progress updates
const ws = new WebSocket('ws://localhost:8000/ws/progress/active');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'progress_update') {
        const progress = data.data;
        console.log(`Progress: ${progress.overall_progress.toFixed(1)}%`);
        console.log(`Status: ${progress.status}`);

        // Update your UI here
        updateProgressBar(progress.overall_progress);
        updateStatus(progress.status);
    }
};
```

#### Option C: HTTP Polling
```javascript
// Poll for progress updates every 3 seconds
setInterval(async () => {
    try {
        const response = await fetch('http://localhost:8000/ws/progress/active');
        const data = await response.json();

        if (data.active_workflows && data.active_workflows.length > 0) {
            const workflow = data.active_workflows[0];
            console.log(`Progress: ${workflow.overall_progress.toFixed(1)}%`);
            console.log(`Current step: ${workflow.current_step || 'None'}`);

            // Update UI
            document.getElementById('progress').textContent = `${workflow.overall_progress.toFixed(1)}%`;
        }
    } catch (error) {
        console.error('Polling error:', error);
    }
}, 3000);
```

## 🔍 Using the System

### Search Your Documents

```python
from services.embedding_service import EmbeddingService

# Initialize embedding service
embedding_service = EmbeddingService(db, vdb)

# Search for relevant content
results = embedding_service.search_similar_chunks(
    collection_name=result.collection_name,
    query="What is retrieval-augmented generation?",
    top_k=5
)

print(f"🔍 Found {len(results)} similar chunks:")
for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result['score']:.3f}")
    print(f"   Content: {result['metadata']['content'][:100]}...")
```

### Generate Answers with LLM

```python
from llm import get_llm

# Get relevant context
context_chunks = results[:3]  # Top 3 most relevant chunks
context = "\n".join([chunk['metadata']['content'] for chunk in context_chunks])

# Generate answer using LLM
llm = get_llm("openai_4o")
messages = [
    {"role": "system", "content": "Answer the question based on the provided context."},
    {"role": "user", "content": f"Context: {context}\n\nQuestion: Explain how RAG works"}
]

answer = await llm.generate(messages)
print(f"🤖 Answer: {answer}")
```

## 📊 Understanding Progress Information

### Progress Data Structure

```json
{
  "workflow_id": "workflow_1699123456_12345",
  "test_id": "test_123",
  "project_id": "proj_456",
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
      "completed_items": 5,
      "metadata": {}
    },
    "chunking": {
      "name": "Content Chunking",
      "progress_percentage": 85.0,
      "status": "running",
      "total_items": 150,
      "completed_items": 127,
      "metadata": {"current_source": "document.pdf"}
    },
    "embedding": {
      "name": "Vector Embedding",
      "progress_percentage": 0.0,
      "status": "pending",
      "total_items": 150,
      "completed_items": 0,
      "metadata": {}
    }
  }
}
```

### Progress Status Values

- **pending**: Step is waiting to start
- **running**: Step is currently executing
- **completed**: Step finished successfully
- **failed**: Step encountered an error

### Common Progress Patterns

#### Fast Completion (Small Documents)
```
0% → 25% (Extraction) → 50% (Chunking) → 100% (Embedding)
Duration: 10-30 seconds
```

#### Slow Completion (Large Documents)
```
0% → 10% (Extraction) → 40% (Chunking) → 100% (Embedding)
Duration: 2-5 minutes
```

#### Web Crawling (Multiple URLs)
```
0% → 60% (Extraction) → 80% (Chunking) → 100% (Embedding)
Duration: 1-3 minutes
```

## 🛠️ Configuration Guide

### Chunking Configuration

#### For Different Content Types:

**Small Documents** (< 1000 characters)
```json
{
  "chunk_size": 500,
  "overlap": 50,
  "type": "recursive"
}
```

**Large Documents** (> 5000 characters)
```json
{
  "chunk_size": 1500,
  "overlap": 200,
  "type": "recursive"
}
```

**Code Files**
```json
{
  "chunk_size": 800,
  "overlap": 100,
  "type": "recursive"
}
```

**Technical Documentation**
```json
{
  "chunk_size": 2000,
  "overlap": 300,
  "type": "recursive"
}
```

### Embedding Models

#### Choose the Right Model:

**General Purpose** (Default)
```json
"embedding_model": "openai_text_embedding_large_3"
```
- 3072 dimensions
- Best quality
- Good performance balance

**Performance Optimized**
```json
"embedding_model": "openai_text_embedding_small_3"
```
- 1536 dimensions
- Faster processing
- Lower memory usage

**Legacy Support**
```json
"embedding_model": "openai_text_embedding_ada_002"
```
- 1536 dimensions
- Compatible with existing systems
- Proven performance

## 🔧 API Usage Examples

### Process Files and URLs

```bash
# Process multiple sources
curl -X POST "http://localhost:8000/workflow/process-corpus" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "corpus_id": "my-corpus",
    "file_paths": [
      "data/documents/manual.pdf",
      "data/documents/api-guide.md"
    ],
    "urls": [
      "https://example.com/docs",
      "https://example.com/api-reference"
    ],
    "crawl_depth": 1,
    "embedding_model_name": "openai_text_embedding_large_3"
  }'
```

### Monitor Workflow Progress

```bash
# Get current progress
curl "http://localhost:8000/workflow/progress/dashboard"

# Get specific workflow progress
curl "http://localhost:8000/ws/progress/active"
```

### Search Collections

```bash
# Search for similar content
curl -X POST "http://localhost:8000/workflow/test/{test_id}/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does RAG work?",
    "top_k": 5
  }'
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: Module not found
# Solution: Install dependencies
uv sync

# Error: Import path issues
# Solution: Run from project root
cd /path/to/rag-eval-core
python examples/workflow_example.py
```

#### 2. OpenAI API Issues
```bash
# Error: API key not set
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"

# Error: Rate limit exceeded
# Solution: Reduce batch size or add delays
```

#### 3. WebSocket Connection Issues
```bash
# Error: Connection refused
# Solution: Start the server first
python main.py

# Error: Connection closed
# Solution: Check server logs for errors
```

#### 4. Database Issues
```bash
# Error: Database locked
# Solution: Check if another instance is running
# Close other connections and try again
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your workflow
# Check console output for detailed information
```

### Performance Issues

#### Slow Processing
1. **Reduce batch size** for embedding (default: 100)
2. **Increase chunk size** for large documents
3. **Limit crawl depth** for web content (default: 1)

#### Memory Issues
1. **Process files individually** for very large files
2. **Use smaller embedding models** (small_3 instead of large_3)
3. **Reduce concurrent operations** if needed

## 📈 Best Practices

### Workflow Design

1. **Start Small**: Begin with a few documents to test your setup
2. **Monitor Progress**: Use the dashboard to understand processing times
3. **Iterate Configuration**: Adjust chunk sizes based on your content
4. **Batch Similar Content**: Group similar documents for better search results

### Performance Optimization

1. **Use Appropriate Chunk Sizes**: 1000-2000 characters for most content
2. **Configure Overlap**: 200 characters for good context preservation
3. **Choose Right Model**: Use small_3 for speed, large_3 for quality
4. **Monitor Resources**: Watch memory and CPU usage during processing

### Error Handling

1. **Check Logs**: Monitor server logs for detailed error information
2. **Validate Inputs**: Ensure file paths and URLs are accessible
3. **Test Connections**: Verify database and API connectivity
4. **Graceful Degradation**: Handle API failures without stopping workflow

## 🎓 Learning Resources

### Documentation
- **Main README**: `README.md` - Complete system overview
- **Workflow Guide**: `WORKFLOW_README.md` - Detailed workflow documentation
- **API Reference**: http://localhost:8000/docs - Interactive API documentation

### Examples
- **Basic Workflow**: `examples/workflow_example.py` - Simple usage example
- **Progress Tracking**: `examples/progress_example.py` - Monitoring demonstration
- **System Tests**: `test_system.py` - Integration tests

### Code Structure
- **Services**: `services/` - Core business logic
- **Handlers**: `handlers/` - API endpoints
- **Repositories**: `repos/` - Data access layer
- **Database**: `db/` - Database schema and connection

## 🆘 Getting Help

### Community Support
- Check existing issues and discussions
- Create detailed bug reports with logs
- Share your use cases and configurations

### Debugging Steps
1. **Run system tests**: `python test_system.py`
2. **Check server logs** for error details
3. **Verify environment variables** are set correctly
4. **Test individual components** before full workflows

### Common Solutions
- **Import errors**: Run from project root directory
- **API errors**: Check server is running and accessible
- **Progress issues**: Verify WebSocket or HTTP connectivity
- **Performance issues**: Adjust batch sizes and chunk configurations

## 🎯 Next Steps

1. **Complete the Quick Start** guide above
2. **Experiment with different configurations** for your use case
3. **Monitor performance** using the progress dashboard
4. **Scale up** to larger document collections
5. **Integrate with your application** using the REST API

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the example code for usage patterns
3. Consult the API documentation at http://localhost:8000/docs
4. Examine server logs for detailed error information

---

**Happy RAG evaluating!** 🎉

The system is designed to be intuitive and powerful. Start simple, monitor progress, and scale as needed. The live progress tracking will help you understand and optimize your workflows.
