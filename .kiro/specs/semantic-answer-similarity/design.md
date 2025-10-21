# Design Document

## Overview

This feature adds semantic similarity measurement between reference answers and LLM-generated answers in the RAG evaluation pipeline. The implementation leverages the existing embedding infrastructure (OpenAI embeddings) configured per test to calculate cosine similarity between answer embeddings. This provides a semantic comparison metric that complements existing lexical metrics (BLEU, ROUGE) without requiring additional large models or GPU resources.

The semantic similarity score will be calculated during the evaluation pipeline and stored alongside other metrics in the database, making it available for analysis and comparison across test runs.

## Architecture

### High-Level Flow

```
1. RAG Evaluation Service generates answer
2. Extract reference answer and generated answer
3. Use test's configured embedding model to embed both answers
4. Calculate cosine similarity between embeddings
5. Store semantic similarity score in database
6. Return score with other evaluation metrics
```

### Component Interaction

```
RAGEvalService
    ↓ (uses)
OpenAIEmbeddings (configured per test)
    ↓ (generates)
Answer Embeddings (reference + generated)
    ↓ (calculates)
Cosine Similarity Score
    ↓ (stores)
Database (evals table)
```

## Components and Interfaces

### 1. Database Schema Changes

**Modified Table: `evals`**

Add new column:
- `semantic_similarity REAL` - Cosine similarity score between reference and generated answers (0.0 to 1.0)

**Migration Strategy:**
- Add column using ALTER TABLE in existing migration logic in `db/db.py`
- Column allows NULL for backward compatibility
- Migration executes during database initialization

### 2. Semantic Similarity Calculator

**New Module: `metrics/semantic_similarity.py`**

```python
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
```

**Implementation Details:**
- Use numpy for efficient vector operations
- Handle edge cases (zero vectors, different dimensions)
- Return normalized score between 0 and 1
- Raise ValueError for invalid inputs

### 3. RAG Evaluation Service Enhancement

**Modified: `services/rag_eval_service.py`**

**New Method:**
```python
async def calculate_semantic_similarity(
    self,
    reference_answer: str,
    generated_answer: str,
    embedding_model: OpenAIEmbeddings
) -> float:
    """
    Calculate semantic similarity between reference and generated answers.
    
    Args:
        reference_answer: Ground truth answer from QA pair
        generated_answer: LLM-generated answer
        embedding_model: Embedding model instance from test config
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
```

**Modified Method: `generate_and_evaluate`**
- Add semantic similarity calculation step after answer generation
- Pass embedding model from test configuration
- Include semantic similarity in returned metrics
- Handle errors gracefully with logging

**Modified Method: `save_evaluation_to_db`**
- Add `semantic_similarity` parameter
- Include semantic_similarity in INSERT statement
- Update column list and values tuple

### 4. Embedding Model Access

**Strategy:**
- Reuse existing `OpenAIEmbeddings` instance from test configuration
- Retrieve embedding model name from test config
- Initialize embedding model if not already available
- Use batch embedding for efficiency (embed both answers together)

### 5. Repository Layer Updates

**Modified: `repos/eval_repo.py`**

**Updated Methods:**
- `get_by_test_run_id`: Include semantic_similarity in SELECT
- `get_full_by_run_and_qa`: Include semantic_similarity in SELECT
- Return semantic_similarity in result dictionaries

## Data Models

### Evaluation Record (Enhanced)

```python
{
    "id": str,
    "test_run_id": str,
    "qa_pair_id": str,
    
    # Lexical metrics
    "bleu": float,
    "rouge_l": float,
    "rouge_l_precision": float,
    "rouge_l_recall": float,
    "squad_em": float,
    "squad_token_f1": float,
    "content_f1": float,
    "lexical_aggregate": float,
    
    # LLM-judged metrics
    "answer_relevance": float,
    "context_relevance": float,
    "groundedness": float,
    "llm_judged_overall": float,
    
    # NEW: Semantic similarity
    "semantic_similarity": float,  # 0.0 to 1.0
    
    # Answer and reasoning
    "answer": str,
    "answer_relevance_reasoning": str,
    "context_relevance_reasoning": str,
    "groundedness_reasoning": str,
    ...
}
```

### Semantic Similarity Calculation Flow

```python
# Input
reference_answer: str = "Paris is the capital of France."
generated_answer: str = "The capital of France is Paris."
embedding_model: OpenAIEmbeddings  # From test config

# Step 1: Generate embeddings (batch operation)
embeddings = await embedding_model.embed_texts([
    reference_answer,
    generated_answer
])
ref_embedding = embeddings[0]  # List[float], length 3072 or 1536
gen_embedding = embeddings[1]  # List[float], length 3072 or 1536

# Step 2: Calculate cosine similarity
similarity = cosine_similarity(ref_embedding, gen_embedding)
# Output: 0.95 (high semantic similarity)
```

## Error Handling

### Error Scenarios

1. **Empty Answers**
   - Handle empty reference or generated answers
   - Return 0.0 similarity for empty strings
   - Log warning message

2. **Embedding Generation Failure**
   - Catch exceptions from embedding API
   - Log error with context
   - Return None for semantic_similarity (stored as NULL)
   - Continue with other metrics

3. **Dimension Mismatch**
   - Validate embedding dimensions match
   - Raise ValueError if mismatch detected
   - Log error with embedding dimensions

4. **Database Migration Failure**
   - Catch ALTER TABLE exceptions
   - Log error message
   - Allow application to continue (best-effort migration)

### Error Handling Strategy

```python
try:
    semantic_similarity = await self.calculate_semantic_similarity(
        reference_answer=reference_answer,
        generated_answer=generated_answer,
        embedding_model=embedding_model
    )
except Exception as e:
    logger.error(f"Failed to calculate semantic similarity: {e}")
    semantic_similarity = None  # Will be stored as NULL
```

## Testing Strategy

### Unit Tests

**Test File: `metrics/test_semantic_similarity.py`**

Test cases:
1. Identical texts → similarity ≈ 1.0
2. Completely different texts → similarity < 0.5
3. Semantically similar texts → similarity > 0.7
4. Empty vectors → handle gracefully
5. Different dimension vectors → raise ValueError
6. Zero vectors → handle gracefully

**Test File: `services/test_rag_eval_service.py`**

Test cases:
1. Semantic similarity calculation with valid inputs
2. Semantic similarity with empty answers
3. Semantic similarity with embedding failure
4. Integration with generate_and_evaluate pipeline
5. Database storage of semantic similarity

### Integration Tests

**Test File: `test_semantic_similarity_integration.py`**

Test scenarios:
1. End-to-end evaluation with semantic similarity
2. Database migration adds column successfully
3. Retrieval of evaluation records includes semantic similarity
4. Batch evaluation calculates semantic similarity for all pairs
5. Backward compatibility with existing records (NULL values)

### Manual Testing

1. Run evaluation on sample QA pairs
2. Verify semantic similarity scores are reasonable
3. Compare with lexical metrics (BLEU, ROUGE)
4. Test with different embedding models (large vs small)
5. Verify performance on laptop hardware

## Performance Considerations

### Optimization Strategies

1. **Batch Embedding**
   - Embed reference and generated answers together
   - Single API call instead of two
   - Reduces latency by ~50%

2. **Reuse Embedding Model**
   - Use existing embedding model instance from test config
   - Avoid redundant model initialization
   - Share connection pool across evaluations

3. **Efficient Vector Operations**
   - Use numpy for cosine similarity calculation
   - Vectorized operations instead of loops
   - O(n) time complexity where n = embedding dimensions

4. **Caching Strategy**
   - Consider caching reference answer embeddings (future enhancement)
   - Reference answers don't change across test runs
   - Could reduce embedding API calls by 50%

### Performance Targets

- **Embedding Generation**: < 1 second per answer pair (2 embeddings)
- **Cosine Similarity Calculation**: < 1 millisecond
- **Total Overhead**: < 2 seconds per QA pair evaluation
- **Memory Usage**: < 50 MB additional (embedding vectors)
- **Hardware Requirements**: No GPU required, runs on CPU

### Scalability

- **Batch Evaluation**: Process multiple QA pairs sequentially
- **Concurrent Requests**: Embedding API supports concurrent requests
- **Rate Limiting**: Handled by existing retry mechanism in OpenAIEmbeddings
- **Database Performance**: Single column addition, minimal impact on queries

## Implementation Notes

### Cosine Similarity Formula

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)

Where:
- A · B = dot product of vectors A and B
- ||A|| = magnitude (L2 norm) of vector A
- ||B|| = magnitude (L2 norm) of vector B
```

### Normalization

- OpenAI embeddings are already normalized (unit vectors)
- Cosine similarity will be in range [-1, 1]
- For text embeddings, typically in range [0, 1]
- No additional normalization needed

### Edge Cases

1. **Identical Answers**: similarity = 1.0
2. **Opposite Meanings**: similarity ≈ 0.0 (rare for answers)
3. **Empty Answer**: similarity = 0.0 (by convention)
4. **Very Short Answers**: May have lower similarity due to less semantic content
5. **Very Long Answers**: Similarity reflects overall semantic alignment

## Dependencies

### Existing Dependencies (No Changes)
- `openai` - For embedding generation
- `numpy` - For vector operations (already used in metrics)
- `chromadb` - Vector database (not used for this feature)

### No New Dependencies Required
- All functionality uses existing libraries
- Cosine similarity implemented with numpy
- Embedding generation uses existing OpenAIEmbeddings class

## Migration Path

### Database Migration

```python
# In db/db.py, add to migration section:

# Ensure evals.semantic_similarity exists
cur = self.conn.execute("PRAGMA table_info('evals')")
cols = [row[1] for row in cur.fetchall()]
if 'semantic_similarity' not in cols:
    with self._tx():
        self.conn.execute("ALTER TABLE evals ADD COLUMN semantic_similarity REAL")
```

### Backward Compatibility

- Existing evaluation records will have NULL semantic_similarity
- New evaluations will populate the field
- API responses handle NULL values gracefully
- Frontend can check for NULL and display "N/A" or hide metric

### Rollout Strategy

1. Deploy database migration (automatic on startup)
2. Deploy updated RAGEvalService with semantic similarity calculation
3. New evaluations automatically include semantic similarity
4. Existing evaluations remain unchanged (NULL values)
5. Optional: Re-run evaluations to populate semantic similarity for historical data

## Future Enhancements

1. **Reference Answer Caching**
   - Cache embeddings for reference answers
   - Reduce API calls by 50% for repeated evaluations
   - Implement cache invalidation strategy

2. **Alternative Similarity Metrics**
   - Euclidean distance
   - Manhattan distance
   - Angular distance

3. **Embedding Model Comparison**
   - Compare semantic similarity across different embedding models
   - Analyze correlation with human judgments

4. **Aggregate Metric Update**
   - Include semantic similarity in aggregate score calculation
   - Determine optimal weight for semantic similarity

5. **Visualization**
   - Plot semantic similarity vs lexical metrics
   - Identify cases where semantic and lexical metrics diverge
   - Highlight potential issues (paraphrasing, hallucination)
