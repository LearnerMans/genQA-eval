# Quick Start: RAG Evaluation with GPT-5

## Setup (2 minutes)

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure API Key
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-key-here
```

That's it! The API key will be automatically loaded from `.env`.

## Usage

### Basic Example

```python
from metrics import evaluate_rag, format_evaluation_report

# Your RAG system output
query = "What is machine learning?"
contexts = [
    "Machine learning is a subset of AI that enables systems to learn from data.",
    "ML algorithms improve their performance with experience."
]
answer = "Machine learning is a branch of AI where systems learn from data."

# Evaluate with GPT-5
result = evaluate_rag(query, contexts, answer)

# View results
print(format_evaluation_report(result))
print(f"Overall Score: {result.overall_score}/3.0")
```

### Run Example Script

```bash
uv run python example_rag_evaluation.py
```

## What Gets Evaluated?

Three dimensions (each scored 0-3):

1. **Context Relevance** - Are the contexts relevant to the query?
2. **Groundedness** - Is the answer faithful to the contexts? (detects hallucinations)
3. **Answer Relevance** - Does the answer fully address the query?

Each includes:
- Numeric score (0-3)
- Detailed explanation
- Specific metrics (claim counts, per-context scores)

## Key Features

- **Uses GPT-5** - Latest OpenAI model for evaluation
- **Structured Output** - Type-safe Pydantic models
- **Detailed Explanations** - Understand why each score was given
- **Easy Integration** - Drop into existing evaluation pipelines
- **Environment Config** - API key loaded from `.env` automatically

## Integration Example

```python
from metrics import evaluate_rag

def evaluate_my_rag_output(query, contexts, answer):
    """Evaluate and store results."""
    evaluation = evaluate_rag(query, contexts, answer)

    # Store in your database
    store_results(
        overall_score=evaluation.overall_score,
        context_score=evaluation.context_relevance.score,
        groundedness=evaluation.groundedness.score,
        answer_score=evaluation.answer_relevance.score
    )

    return evaluation
```

## Model Variants

Choose based on your needs:

```python
# Standard GPT-5 (recommended)
result = evaluate_rag(query, contexts, answer, model="gpt-5")

# Faster & cheaper variants
result = evaluate_rag(query, contexts, answer, model="gpt-5-mini")
result = evaluate_rag(query, contexts, answer, model="gpt-5-nano")
```

## Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure you created `.env` file (copy from `.env.example`)
- Add your API key: `OPENAI_API_KEY=sk-proj-...`
- File should be in project root

### "Module not found"
```bash
uv sync  # Reinstall dependencies
```

## More Information

- Full documentation: [metrics/RAG_EVALUATOR_README.md](metrics/RAG_EVALUATOR_README.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- Test examples: [metrics/test_rag_evaluator.py](metrics/test_rag_evaluator.py)
- Integration guide: [metrics/integration_example_llm_judge.py](metrics/integration_example_llm_judge.py)

## Need Help?

Check the full README for:
- API reference
- Best practices
- Advanced usage
- Cost optimization tips

Happy evaluating! 🎯
