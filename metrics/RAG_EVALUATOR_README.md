# RAG Evaluator with GPT-5

LLM-as-a-Judge evaluation framework for RAG (Retrieval-Augmented Generation) systems using GPT-5.

## Overview

This module implements the **RAG Triad** evaluation framework, which assesses RAG systems across three critical dimensions:

1. **Context Relevance** - Are the retrieved contexts relevant to answering the query?
2. **Groundedness** - Is the generated answer faithful to the retrieved contexts?
3. **Answer Relevance** - Does the answer fully address the user's query?

## Installation

Dependencies are managed via `pyproject.toml`. Install using:

```bash
uv sync
```

Or add the required packages:

```bash
uv add instructor numpy pydantic openai
```

## Setup

Create a `.env` file in the project root with your OpenAI API key:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
OPENAI_API_KEY=your-api-key-here
```

The API key will be automatically loaded from the `.env` file when you use the evaluator.

**Alternative:** You can also set it as an environment variable:

```bash
# Linux/Mac
export OPENAI_API_KEY='your-api-key-here'

# Windows CMD
set OPENAI_API_KEY=your-api-key-here

# Windows PowerShell
$env:OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Basic Usage

```python
from metrics import evaluate_rag, format_evaluation_report

result = evaluate_rag(
    query="What are the symptoms of type 2 diabetes?",
    contexts=[
        "Type 2 diabetes symptoms include increased thirst, frequent urination...",
        "Type 2 diabetes often develops slowly. Some people have no symptoms initially.",
        "Regular blood sugar monitoring is important for diabetes management."
    ],
    answer="Common symptoms include increased thirst, frequent urination, fatigue..."
)

# Print formatted report
print(format_evaluation_report(result))

# Access individual scores
print(f"Overall: {result.overall_score}/3.0")
print(f"Context Relevance: {result.context_relevance.score}")
print(f"Groundedness: {result.groundedness.score}")
print(f"Answer Relevance: {result.answer_relevance.score}")
```

### Advanced Usage

```python
from metrics.rag_evaluator import evaluate_rag, score_to_numeric

# Use specific GPT-5 model variant
result = evaluate_rag(
    query="Your query here",
    contexts=["context 1", "context 2"],
    answer="Your generated answer",
    model="gpt-5-mini",  # Options: gpt-5, gpt-5-mini, gpt-5-nano
    temperature=0.0  # 0.0 for deterministic evaluation
)

# Convert scores to numeric
context_score = score_to_numeric(result.context_relevance.score)
groundedness_score = score_to_numeric(result.groundedness.score)
answer_score = score_to_numeric(result.answer_relevance.score)

print(f"Numeric scores: {context_score}, {groundedness_score}, {answer_score}")
```

### Integration with Your RAG Pipeline

```python
from metrics import evaluate_rag

def evaluate_my_rag_system(query: str) -> dict:
    # Your RAG system
    contexts = retrieve_contexts(query)
    answer = generate_answer(query, contexts)

    # Evaluate with GPT-5
    evaluation = evaluate_rag(query, contexts, answer)

    return {
        "query": query,
        "answer": answer,
        "evaluation": {
            "overall_score": evaluation.overall_score,
            "context_relevance": evaluation.context_relevance.score.value,
            "groundedness": evaluation.groundedness.score.value,
            "answer_relevance": evaluation.answer_relevance.score.value,
            "explanations": {
                "context": evaluation.context_relevance.explanation,
                "groundedness": evaluation.groundedness.explanation,
                "answer": evaluation.answer_relevance.explanation
            }
        }
    }
```

## Scoring System

Each dimension is scored on a **0-3 scale**:

- **3 (Excellent)**: Exceptional quality, meets all criteria
- **2 (Good)**: High quality with minor issues
- **1 (Average)**: Moderate quality, significant gaps
- **0 (Bad)**: Poor quality, fails criteria

### Context Relevance (0-3)

Evaluates whether retrieved contexts can answer the query:
- **3**: Contexts highly relevant, can fully answer query
- **2**: Contexts partially relevant, provide some coverage
- **1**: Contexts have slight connection but limited usefulness
- **0**: Contexts irrelevant to query

### Groundedness (0-3)

Evaluates factual faithfulness to contexts:
- **3**: All claims fully supported by contexts
- **2**: Mostly supported with minor unsupported details
- **1**: Some unsupported claims or hallucinations
- **0**: Multiple hallucinations, completely unsupported

### Answer Relevance (0-3)

Evaluates how well the answer addresses the query:
- **3**: Completely addresses query
- **2**: Mostly addresses query with minor gaps
- **1**: Partially addresses query
- **0**: Doesn't address query or refuses

## Response Structure

```python
class RAGEvaluation(BaseModel):
    context_relevance: ContextRelevance  # Score + explanation + per-context scores
    groundedness: Groundedness           # Score + explanation + claim analysis
    answer_relevance: AnswerRelevance    # Score + explanation
    overall_score: float                 # Average of all three scores
```

## Model Options

GPT-5 is available in multiple variants:

- **`gpt-5`** - Main GPT-5 model (recommended for production)
- **`gpt-5-mini`** - Faster, more cost-effective
- **`gpt-5-nano`** - Most efficient, lowest cost
- **`gpt-5-2025-08-07`** - Specific dated version

All models support a **400,000 token context window**.

## Examples

See [`test_rag_evaluator.py`](./test_rag_evaluator.py) for comprehensive examples:

```bash
# Run example tests (requires OPENAI_API_KEY)
uv run python metrics/test_rag_evaluator.py
```

## API Reference

### `evaluate_rag()`

```python
def evaluate_rag(
    query: str,
    contexts: List[str],
    answer: str,
    model: str = "gpt-5",
    temperature: float = 0.0
) -> RAGEvaluation
```

**Parameters:**
- `query`: User's question/query
- `contexts`: List of retrieved context passages
- `answer`: Generated answer from RAG system
- `model`: GPT-5 model variant (default: "gpt-5")
- `temperature`: Sampling temperature (default: 0.0)

**Returns:** `RAGEvaluation` object with scores and explanations

### `format_evaluation_report()`

```python
def format_evaluation_report(evaluation: RAGEvaluation) -> str
```

Formats evaluation results as a human-readable report.

### `score_to_numeric()`

```python
def score_to_numeric(score: Score) -> float
```

Converts Score enum to numeric value (0.0, 1.0, 2.0, or 3.0).

## Best Practices

1. **Use temperature=0.0** for deterministic, consistent evaluations
2. **Evaluate on diverse examples** to get reliable metrics
3. **Review explanations** to understand failure modes
4. **Monitor per-context scores** to improve retrieval
5. **Track groundedness claims** to detect hallucinations
6. **Compare across model variants** to optimize cost/quality

## Troubleshooting

### API Key Issues

```
OpenAIError: The api_key client option must be set
```

**Solution:** Create a `.env` file in the project root with your API key:
```
OPENAI_API_KEY=your-api-key-here
```

Or set the `OPENAI_API_KEY` environment variable.

### Model Not Found

```
openai.NotFoundError: model 'gpt-5' not found
```

**Solution:** Ensure you have access to GPT-5 in your OpenAI account. Try `gpt-4o` as fallback.

### Import Errors

```
ModuleNotFoundError: No module named 'instructor'
```

**Solution:** Run `uv sync` to install dependencies.

## References

- [RAG Triad Framework](https://www.trulens.org/trulens_eval/core_concepts_rag_triad/)
- [OpenAI GPT-5 Documentation](https://platform.openai.com/docs/models/gpt-5)
- [Instructor Library](https://github.com/jxnl/instructor)

## License

Part of the RAG Eval Core project.
