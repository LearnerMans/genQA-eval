# Metrics Package

A comprehensive text evaluation metrics package for RAG (Retrieval-Augmented Generation) systems. This package provides implementations of common NLG (Natural Language Generation) evaluation metrics without external dependencies.

## Features

- **BLEU**: Bilingual Evaluation Understudy with multi-reference support and Chen & Cherry smoothing
- **ROUGE-L**: Longest Common Subsequence based metric
- **SQuAD EM**: Exact Match scoring
- **SQuAD Token F1**: Token-level F1 score
- **Content F1**: Content-word based F1 for hallucination/verbosity detection
- **Aggregate Scoring**: Weighted combination of multiple metrics

## Installation

No additional dependencies required - all functionality is built using Python standard library.

## Quick Start

### Basic Usage

```python
from metrics import bleu, rouge_l, squad_em, squad_token_f1, score_texts

# Single reference
candidate = "Paris is the capital of France."
reference = "The capital of France is Paris."

# Calculate BLEU score
bleu_result = bleu(candidate, reference)
print(f"BLEU: {bleu_result['bleu']:.4f}")

# Calculate ROUGE-L score
rouge_result = rouge_l(candidate, reference)
print(f"ROUGE-L F1: {rouge_result['f1']:.4f}")

# Calculate SQuAD metrics
em = squad_em(candidate, reference)
token_f1 = squad_token_f1(candidate, reference)
print(f"Exact Match: {em:.4f}")
print(f"Token F1: {token_f1:.4f}")
```

### Multi-Reference Evaluation

```python
from metrics import score_texts

candidate = "The cat sat on the mat."
references = [
    "The cat is sitting on the mat.",
    "A cat sits on the mat.",
    "The cat was on the mat."
]

# Get all metrics at once
result = score_texts(candidate, references)

print(f"BLEU: {result['BLEU']:.4f}")
print(f"ROUGE-L: {result['ROUGE_L']:.4f}")
print(f"SQuAD EM: {result['SQuAD_EM']:.4f}")
print(f"SQuAD Token F1: {result['SQuAD_token_F1']:.4f}")
print(f"Content F1: {result['ContentF1']:.4f}")
print(f"Aggregate: {result['Aggregate']:.4f}")
```

### RAG System Integration

```python
from metrics import score_texts

# Your RAG system generates an answer
llm_answer = "Paris is the capital of France and largest city."
ground_truth = "The capital of France is Paris."

# Evaluate the answer
scores = score_texts(llm_answer, ground_truth)

# Check for verbosity/hallucination
if scores['ContentF1'] < 0.7:
    print("Warning: Answer may contain extra/hallucinated content")

# Overall quality check
if scores['Aggregate'] > 0.7:
    print("High quality answer")
elif scores['Aggregate'] > 0.5:
    print("Acceptable answer")
else:
    print("Low quality answer")
```

## Metrics Description

### BLEU (Bilingual Evaluation Understudy)

Measures n-gram overlap between candidate and reference texts. Returns:
- `bleu`: Overall BLEU score (0-1)
- `by_n`: Per-n-gram precisions
- `bp`: Brevity penalty

**Parameters:**
- `max_n`: Maximum n-gram order (default: 4)
- `smooth`: Apply Chen & Cherry smoothing (default: True)
- `weights`: Per-n-gram weights (default: uniform)

### ROUGE-L (Longest Common Subsequence)

Measures the longest common subsequence between texts. Returns:
- `f1`: F1 score (0-1)
- `precision`: Precision
- `recall`: Recall
- `lcs`: Length of LCS

**Parameters:**
- `beta`: F-score beta parameter (default: 1.0 for F1)

### SQuAD Exact Match (EM)

Binary metric checking if normalized texts match exactly. Returns:
- Score of 1.0 if exact match with any reference, 0.0 otherwise

### SQuAD Token F1

Token-level overlap F1 score (commonly used for QA tasks). Returns:
- F1 score (0-1) based on token overlap

### Content F1

Evaluates content-word overlap (filters short/digit tokens). Useful for detecting:
- Hallucinations (low precision)
- Missing information (low recall)
- Verbosity (precision/recall imbalance)

Returns:
- `f1`: F1 score
- `precision`: Precision
- `recall`: Recall

### Aggregate Score

Weighted combination of multiple metrics. Default weights:
- BLEU: 0.30
- ROUGE-L: 0.40
- Content F1: 0.20
- Exact Match: 0.10

**Customize weights:**
```python
result = score_texts(
    candidate,
    reference,
    aggregate_weights=(0.25, 0.35, 0.30, 0.10)  # (BLEU, ROUGE, ContentF1, EM)
)
```

## API Reference

### `bleu(candidate, references, max_n=4, smooth=True, weights=None)`

Calculate BLEU score with multi-reference support.

### `rouge_l(candidate, references, beta=1.0)`

Calculate ROUGE-L (Longest Common Subsequence) score.

### `squad_em(candidate, references)`

Calculate SQuAD-style Exact Match score.

### `squad_token_f1(candidate, references)`

Calculate SQuAD-style token-level F1 score.

### `content_f1(candidate, references)`

Calculate content-word F1 for hallucination detection.

### `score_texts(candidate, references, max_n=4, smooth=True, aggregate_weights=(0.30, 0.40, 0.20, 0.10))`

Comprehensive evaluation with all metrics and aggregate score.

## Testing

Run the test suite to verify all metrics work correctly:

```bash
cd metrics
python test_metrics.py
```

## Use Cases

### 1. RAG System Evaluation
Evaluate generated answers against ground truth in your RAG pipeline.

### 2. Model Comparison
Compare different LLM outputs using consistent metrics.

### 3. Quality Assurance
Automated testing of text generation quality in CI/CD.

### 4. A/B Testing
Compare different prompts or retrieval strategies.

### 5. Hallucination Detection
Use Content F1 precision to detect when model adds extra information.

## Language Support

All metrics use language-agnostic tokenization based on Unicode word boundaries. They work with:
- English
- Most European languages
- Unicode-based languages (with varying effectiveness)

## Implementation Details

- **No external dependencies**: Uses only Python standard library
- **Multi-reference support**: All metrics support single or multiple references
- **Efficient algorithms**: Optimized implementations (e.g., space-optimized LCS)
- **Smoothing**: Chen & Cherry method 1 for BLEU (handles zero n-gram matches)
- **Normalization**: SQuAD-style normalization for EM/Token F1

## Performance Considerations

- **Time Complexity**: O(nm) for most metrics where n=candidate length, m=reference length
- **Space Complexity**: O(n) for most metrics
- **Scalability**: Suitable for batch evaluation of thousands of examples

## Contributing

When adding new metrics:
1. Add implementation to `text_metrics.py`
2. Export from `__init__.py`
3. Add tests to `test_metrics.py`
4. Update this README

## License

Part of the RAG Eval Core project.
