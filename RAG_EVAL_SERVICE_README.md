# RAG Evaluation Service

Complete pipeline for RAG answer generation and comprehensive evaluation with both lexical and LLM-judged metrics.

## Overview

The `RAGEvalService` provides an end-to-end solution for:

1. **Context Retrieval**: Retrieve relevant contexts from vector database using semantic search
2. **Answer Generation**: Generate answers using LLM with retrieved contexts
3. **Lexical Metrics**: Calculate BLEU, ROUGE-L, SQuAD EM/F1, and Content F1
4. **LLM-Judged Metrics**: Evaluate with GPT-4o for context relevance, groundedness, and answer relevance
5. **Database Storage**: Automatically store all results in the database

## Features

- **Complete Pipeline**: Single function call for generation + evaluation
- **Batch Processing**: Evaluate multiple QA pairs efficiently
- **Custom Prompts**: Support for custom prompt templates
- **Comprehensive Metrics**: Both lexical and LLM-judged evaluation
- **Automatic Storage**: Results saved to database with chunk tracking
- **Async Support**: Built with async/await for performance

## Installation

Ensure you have all required dependencies:

```bash
uv sync
```

Required packages:
- `openai` - For LLM and embeddings
- `chromadb` - For vector database
- `numpy` - For numerical operations
- `python-dotenv` - For environment variables

## Setup

1. **Environment Variables**

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

2. **Database**

The service uses the existing database structure. Make sure you have:
- A populated vector database collection with embeddings
- Test runs in the `test_runs` table
- QA pairs in the `question_answer_pairs` table

## Usage

### Basic Example

```python
import asyncio
from db.db import DB
from vectorDb.db import VectorDb
from services.rag_eval_service import RAGEvalService

async def evaluate_single_qa():
    # Initialize services
    db = DB("data/db.db")
    vector_db = VectorDb("data")

    service = RAGEvalService(db=db, vector_db=vector_db)

    # Run evaluation
    result = await service.generate_and_evaluate(
        test_run_id="your-test-run-id",
        qa_pair_id="your-qa-pair-id",
        query="What are the symptoms of diabetes?",
        reference_answer="Common symptoms include increased thirst, frequent urination, and fatigue.",
        collection_name="medical-docs",
        top_k=10
    )

    print(f"Generated Answer: {result['generated_answer']}")
    print(f"BLEU Score: {result['lexical_metrics']['bleu']:.4f}")
    print(f"LLM Overall Score: {result['llm_judged_metrics']['llm_judged_overall']:.2f}/3.0")

    db.close()

asyncio.run(evaluate_single_qa())
```

### Batch Evaluation

```python
async def batch_evaluate():
    db = DB("data/db.db")
    vector_db = VectorDb("data")

    service = RAGEvalService(db=db, vector_db=vector_db)

    # Get QA pairs from database
    qa_pairs = [
        {"id": "qa1", "question": "What is X?", "answer": "X is..."},
        {"id": "qa2", "question": "What is Y?", "answer": "Y is..."},
    ]

    results = await service.batch_evaluate(
        test_run_id="test-run-123",
        qa_pairs=qa_pairs,
        collection_name="knowledge-base",
        top_k=10
    )

    # Process results
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['qa_pair_id']}: Success")
        else:
            print(f"✗ {result['qa_pair_id']}: {result['error']}")

    db.close()
```

### Custom Prompt Template

```python
custom_prompt = """You are a technical support assistant. Answer the user's question based on the provided documentation.

Documentation:
{contexts}

Question: {query}

Provide a clear, step-by-step answer. If the documentation doesn't cover this, say so explicitly.

Answer:"""

result = await service.generate_and_evaluate(
    test_run_id="test-123",
    qa_pair_id="qa-456",
    query="How do I reset my password?",
    reference_answer="Go to settings, click 'Reset Password', and follow the instructions.",
    collection_name="support-docs",
    prompt_template=custom_prompt,
    temperature=0.5
)
```

## API Reference

### RAGEvalService

#### Constructor

```python
RAGEvalService(
    db: DB,
    vector_db: VectorDb,
    llm: Optional[OpenAILLM] = None,
    embeddings: Optional[OpenAIEmbeddings] = None
)
```

**Parameters:**
- `db`: Database instance
- `vector_db`: Vector database instance
- `llm`: Optional LLM instance (defaults to GPT-4o)
- `embeddings`: Optional embeddings instance (defaults to text-embedding-3-large)

#### Main Methods

##### `generate_and_evaluate()`

Complete pipeline for answer generation and evaluation.

```python
async def generate_and_evaluate(
    test_run_id: str,
    qa_pair_id: str,
    query: str,
    reference_answer: str,
    collection_name: str,
    top_k: int = 10,
    prompt_template: Optional[str] = None,
    temperature: float = 0.7,
    eval_model: str = "gpt-4o"
) -> Dict[str, Any]
```

**Returns:**
```python
{
    'eval_id': str,                    # Database evaluation ID
    'generated_answer': str,           # LLM-generated answer
    'contexts': List[Dict],            # Retrieved contexts with metadata
    'lexical_metrics': {               # Lexical evaluation scores
        'bleu': float,
        'rouge_l': float,
        'rouge_l_precision': float,
        'rouge_l_recall': float,
        'squad_em': float,
        'squad_token_f1': float,
        'content_f1': float,
        'lexical_aggregate': float
    },
    'llm_judged_metrics': {            # LLM-judged evaluation scores (0-3 scale)
        'answer_relevance': float,
        'context_relevance': float,
        'groundedness': float,
        'llm_judged_overall': float
    }
}
```

##### `batch_evaluate()`

Batch evaluation for multiple QA pairs.

```python
async def batch_evaluate(
    test_run_id: str,
    qa_pairs: List[Dict[str, Any]],
    collection_name: str,
    top_k: int = 10,
    prompt_template: Optional[str] = None,
    temperature: float = 0.7,
    eval_model: str = "gpt-4o"
) -> List[Dict[str, Any]]
```

**QA Pair Format:**
```python
{
    'id': str,          # QA pair ID
    'question': str,    # Question text
    'answer': str       # Reference answer
}
```

## Metrics Explained

### Lexical Metrics (0-1 scale)

| Metric | Description |
|--------|-------------|
| **BLEU** | Measures n-gram overlap with reference answer |
| **ROUGE-L** | Longest common subsequence F1 score |
| **SQuAD EM** | Exact match after normalization |
| **SQuAD Token F1** | Token-level F1 score |
| **Content F1** | F1 for content words (hallucination detection) |
| **Lexical Aggregate** | Weighted combination of all lexical metrics |

### LLM-Judged Metrics (0-3 scale)

| Metric | Description |
|--------|-------------|
| **Context Relevance** | Are retrieved contexts relevant to the query? |
| **Groundedness** | Is the answer faithful to the contexts? |
| **Answer Relevance** | Does the answer fully address the query? |
| **LLM Judged Overall** | Average of the three metrics above |

**Score Interpretation:**
- 0 (Bad): Poor quality
- 1 (Average): Acceptable but with issues
- 2 (Good): Good quality with minor issues
- 3 (Excellent): Excellent quality

## Database Schema

Results are stored in the `evals` table:

```sql
CREATE TABLE evals (
  id TEXT PRIMARY KEY,
  test_run_id TEXT NOT NULL,
  qa_pair_id TEXT NOT NULL,

  -- Lexical metrics
  bleu REAL,
  rouge_l REAL,
  rouge_l_precision REAL,
  rouge_l_recall REAL,
  squad_em REAL,
  squad_token_f1 REAL,
  content_f1 REAL,
  lexical_aggregate REAL,

  -- LLM-judged metrics
  answer_relevance REAL,
  context_relevance REAL,
  groundedness REAL,
  llm_judged_overall REAL,

  -- Generated answer
  answer TEXT,

  FOREIGN KEY (test_run_id) REFERENCES test_runs(id),
  FOREIGN KEY (qa_pair_id) REFERENCES question_answer_pairs(id)
);
```

Retrieved chunks are linked in `eval_chunks` table for traceability.

## Error Handling

The service includes comprehensive error handling:

```python
try:
    result = await service.generate_and_evaluate(...)
except ValueError as e:
    # Invalid parameters or no contexts found
    print(f"Configuration error: {e}")
except RuntimeError as e:
    # API errors (OpenAI, ChromaDB, etc.)
    print(f"Runtime error: {e}")
except Exception as e:
    # Other unexpected errors
    print(f"Unexpected error: {e}")
```

## Performance Considerations

- **Context Retrieval**: O(log n) for vector search
- **LLM Generation**: ~2-5 seconds per query
- **Lexical Metrics**: <100ms per evaluation
- **LLM-Judged Metrics**: ~5-10 seconds per evaluation (GPT-4o API call)
- **Database Storage**: <50ms per record

**Batch Processing**: For large batches, consider:
- Rate limiting for OpenAI API
- Parallel processing with `asyncio.gather()`
- Progress tracking and checkpointing

## Examples

See complete examples in [examples/complete_rag_eval_example.py](examples/complete_rag_eval_example.py):

1. Single QA pair evaluation
2. Batch evaluation with database integration
3. Custom prompt templates
4. Result analysis and reporting

## Troubleshooting

### Common Issues

**Issue**: `No contexts found in collection`
- **Solution**: Verify collection name and ensure it's populated with embeddings

**Issue**: `OpenAI API error`
- **Solution**: Check API key in `.env` and verify account has credits

**Issue**: `ValueError: Unsupported model`
- **Solution**: Use supported models: `openai_4o`, `openai_4o_mini`, `openai_4`, `openai_3_5_turbo`

**Issue**: Low metric scores
- **Solution**: Check:
  - Context quality and relevance
  - Prompt template clarity
  - Reference answer quality
  - Model temperature settings

## Integration with Existing Code

The service integrates seamlessly with existing handlers:

```python
# In evals_handler.py
from services.rag_eval_service import RAGEvalService

@router.post("/evals/run")
async def run_evaluation(test_run_id: str, qa_pair_ids: List[str]):
    service = RAGEvalService(db=db, vector_db=vector_db)

    results = []
    for qa_id in qa_pair_ids:
        qa = qa_repo.get_by_id(qa_id)
        result = await service.generate_and_evaluate(
            test_run_id=test_run_id,
            qa_pair_id=qa_id,
            query=qa['question'],
            reference_answer=qa['answer'],
            collection_name=f"test_{test_run_id}"
        )
        results.append(result)

    return {"results": results}
```

## Future Enhancements

Potential improvements:
- Support for other LLM providers (Anthropic, Cohere, etc.)
- Caching for repeated evaluations
- Parallel batch processing
- Real-time progress tracking
- Custom metric weights
- Export to CSV/JSON

## License

This service is part of the RAG Eval Core project.
