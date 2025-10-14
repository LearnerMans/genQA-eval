# Metrics Package - Quick Start Guide

## Installation

No installation required! The package uses only Python standard library.

## Basic Usage (Copy & Paste)

### 1. Simple Evaluation

```python
from metrics import score_texts

candidate = "Your LLM generated answer here"
ground_truth = "The expected answer"

result = score_texts(candidate, ground_truth)

print(f"BLEU: {result['BLEU']:.4f}")
print(f"ROUGE-L: {result['ROUGE_L']:.4f}")
print(f"Overall: {result['Aggregate']:.4f}")
```

### 2. Multiple References

```python
from metrics import score_texts

candidate = "LLM answer"
references = [
    "Reference answer 1",
    "Reference answer 2",
    "Reference answer 3"
]

result = score_texts(candidate, references)
print(f"Best BLEU: {result['BLEU']:.4f}")
```

### 3. Individual Metrics

```python
from metrics import bleu, rouge_l, squad_em, squad_token_f1

candidate = "Your answer"
reference = "Expected answer"

# Just BLEU
bleu_score = bleu(candidate, reference)
print(f"BLEU: {bleu_score['bleu']:.4f}")

# Just ROUGE-L
rouge_score = rouge_l(candidate, reference)
print(f"ROUGE-L: {rouge_score['f1']:.4f}")

# Exact Match (returns 1.0 or 0.0)
em = squad_em(candidate, reference)
print(f"Exact Match: {em}")

# Token F1
token_f1 = squad_token_f1(candidate, reference)
print(f"Token F1: {token_f1:.4f}")
```

### 4. Integration with Your RAG System

```python
from metrics import score_texts

def evaluate_rag_answer(llm_answer, ground_truth):
    """Evaluate a RAG system answer."""
    scores = score_texts(llm_answer, ground_truth)

    return {
        "bleu": scores["BLEU"],
        "rouge": scores["ROUGE_L"],
        "aggregate": scores["Aggregate"],
        "quality": "Good" if scores["Aggregate"] > 0.6 else "Poor"
    }

# Usage
result = evaluate_rag_answer(
    "Paris is the capital of France.",
    "The capital of France is Paris."
)
print(result)
# {'bleu': 0.4729, 'rouge': 0.7143, 'aggregate': 0.6276, 'quality': 'Good'}
```

### 5. Batch Evaluation

```python
from metrics import score_texts

qa_pairs = [
    ("Answer 1", "Ground truth 1"),
    ("Answer 2", "Ground truth 2"),
    ("Answer 3", "Ground truth 3"),
]

results = []
for candidate, reference in qa_pairs:
    result = score_texts(candidate, reference)
    results.append({
        "bleu": result["BLEU"],
        "rouge": result["ROUGE_L"],
        "aggregate": result["Aggregate"]
    })

# Calculate average
avg_score = sum(r["aggregate"] for r in results) / len(results)
print(f"Average Quality: {avg_score:.4f}")
```

## Understanding the Scores

### Score Ranges (0.0 - 1.0)

- **0.9 - 1.0**: Excellent (near perfect match)
- **0.7 - 0.9**: Good (high quality)
- **0.5 - 0.7**: Acceptable (moderate quality)
- **0.3 - 0.5**: Poor (low quality)
- **0.0 - 0.3**: Very Poor (very low quality)

### What Each Metric Measures

| Metric | What it measures | Good for |
|--------|-----------------|----------|
| **BLEU** | N-gram overlap (word sequences) | Overall fluency and accuracy |
| **ROUGE-L** | Longest common subsequence | Sentence structure similarity |
| **SQuAD EM** | Exact match (binary) | Factual correctness |
| **Token F1** | Token overlap | Semantic similarity |
| **Content F1** | Content word overlap | Hallucination detection |
| **Aggregate** | Weighted combination | Overall quality |

### When to Use What

```python
from metrics import score_texts

result = score_texts(candidate, reference)

# Check overall quality
if result["Aggregate"] < 0.5:
    print("⚠️ Low quality answer")

# Check for hallucination/verbosity
if result["ContentF1"] < 0.6:
    print("⚠️ May contain hallucinated or extra content")

# Check for exact correctness (important for factual QA)
if result["SQuAD_EM"] == 1.0:
    print("✓ Exact match!")

# Check structural similarity
if result["ROUGE_L"] > 0.8:
    print("✓ Good structural match")
```

## Testing

Run the test suite:
```bash
cd metrics
python test_metrics.py
```

Run integration examples:
```bash
cd metrics
python integration_example.py
```

## Custom Weights

Adjust importance of different metrics:

```python
from metrics import score_texts

# Default: (BLEU=0.3, ROUGE=0.4, ContentF1=0.2, EM=0.1)
result = score_texts(candidate, reference)

# Custom: Prioritize ROUGE and EM
result = score_texts(
    candidate,
    reference,
    aggregate_weights=(0.2, 0.5, 0.1, 0.2)  # (BLEU, ROUGE, ContentF1, EM)
)
```

## Common Patterns

### Pattern 1: Quality Gate

```python
from metrics import score_texts

def passes_quality_gate(candidate, reference, threshold=0.6):
    """Check if answer meets quality threshold."""
    result = score_texts(candidate, reference)
    return result["Aggregate"] >= threshold

if passes_quality_gate(llm_answer, ground_truth):
    print("✓ Passed quality gate")
else:
    print("✗ Failed quality gate")
```

### Pattern 2: Best Answer Selection

```python
from metrics import score_texts

def select_best_answer(candidates, reference):
    """Select best answer from multiple candidates."""
    best_score = -1
    best_answer = None

    for candidate in candidates:
        result = score_texts(candidate, reference)
        if result["Aggregate"] > best_score:
            best_score = result["Aggregate"]
            best_answer = candidate

    return best_answer, best_score

# Usage
candidates = ["Answer A", "Answer B", "Answer C"]
best, score = select_best_answer(candidates, "Ground truth")
print(f"Best: {best} (score: {score:.4f})")
```

### Pattern 3: Test Run Summary

```python
from metrics import score_texts

def evaluate_test_run(qa_pairs):
    """Evaluate entire test run and return summary."""
    results = []

    for candidate, reference in qa_pairs:
        result = score_texts(candidate, reference)
        results.append(result["Aggregate"])

    return {
        "count": len(results),
        "average": sum(results) / len(results),
        "min": min(results),
        "max": max(results),
        "passed": sum(1 for r in results if r >= 0.6)
    }
```

## Need Help?

- See [README.md](README.md) for detailed documentation
- See [integration_example.py](integration_example.py) for advanced usage
- Run [test_metrics.py](test_metrics.py) to verify installation

## Performance

Typical evaluation times (on standard hardware):
- Single evaluation: < 1ms
- Batch of 100: < 100ms
- Batch of 1000: < 1s

Suitable for:
- Real-time evaluation
- Batch processing
- CI/CD pipelines
- Production monitoring
