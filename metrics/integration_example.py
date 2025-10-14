"""
Example of integrating the metrics package with the RAG Eval Core system.

This demonstrates how to use the metrics to evaluate LLM responses
against ground truth answers in your evaluation pipeline.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import score_texts


class EvalMetricsCalculator:
    """
    Helper class to calculate evaluation metrics for RAG systems.

    This can be integrated into your evaluation pipeline to automatically
    compute BLEU and ROUGE scores (and other metrics) for test runs.
    """

    def __init__(self, aggregate_weights=(0.30, 0.40, 0.20, 0.10)):
        """
        Initialize the calculator with custom weights.

        Args:
            aggregate_weights: Tuple of (BLEU, ROUGE_L, ContentF1, EM) weights
        """
        self.aggregate_weights = aggregate_weights

    def evaluate_answer(self,
                       candidate: str,
                       ground_truth: str | list[str],
                       return_all: bool = False) -> dict:
        """
        Evaluate a candidate answer against ground truth.

        Args:
            candidate: The LLM-generated answer to evaluate
            ground_truth: Ground truth answer(s) - single string or list
            return_all: If True, return all metrics; if False, return only BLEU/ROUGE

        Returns:
            Dictionary with evaluation metrics
        """
        result = score_texts(
            candidate,
            ground_truth,
            aggregate_weights=self.aggregate_weights
        )

        if return_all:
            return result

        # Return only the metrics stored in the database
        return {
            "bleu": result["BLEU"],
            "rouge": result["ROUGE_L"],
            "aggregate": result["Aggregate"],
            # Additional useful metrics
            "squad_em": result["SQuAD_EM"],
            "squad_token_f1": result["SQuAD_token_F1"],
            "content_f1": result["ContentF1"],
        }

    def batch_evaluate(self,
                      qa_pairs: list[tuple[str, str]],
                      return_all: bool = False) -> list[dict]:
        """
        Evaluate multiple QA pairs in batch.

        Args:
            qa_pairs: List of (candidate, ground_truth) tuples
            return_all: If True, return all metrics for each pair

        Returns:
            List of metric dictionaries, one per QA pair
        """
        return [
            self.evaluate_answer(candidate, ground_truth, return_all)
            for candidate, ground_truth in qa_pairs
        ]


def example_usage():
    """Demonstrate usage of the EvalMetricsCalculator."""

    print("=" * 70)
    print("RAG Eval Core - Metrics Integration Example")
    print("=" * 70)

    calculator = EvalMetricsCalculator()

    # Example 1: Single evaluation
    print("\n1. Single Answer Evaluation:")
    print("-" * 70)

    candidate = "Paris is the capital and largest city of France."
    ground_truth = "The capital of France is Paris."

    result = calculator.evaluate_answer(candidate, ground_truth)

    print(f"Candidate: {candidate}")
    print(f"Ground Truth: {ground_truth}")
    print(f"\nMetrics:")
    print(f"  BLEU:          {result['bleu']:.4f}")
    print(f"  ROUGE-L:       {result['rouge']:.4f}")
    print(f"  Aggregate:     {result['aggregate']:.4f}")
    print(f"  SQuAD EM:      {result['squad_em']:.4f}")
    print(f"  SQuAD Token F1: {result['squad_token_f1']:.4f}")
    print(f"  Content F1:    {result['content_f1']:.4f}")

    # Example 2: Multi-reference evaluation
    print("\n\n2. Multi-Reference Evaluation:")
    print("-" * 70)

    candidate = "Machine learning is a subset of AI."
    references = [
        "Machine learning is a subset of artificial intelligence.",
        "ML is a subfield of AI.",
        "Artificial intelligence includes machine learning as a subset."
    ]

    result = calculator.evaluate_answer(candidate, references)

    print(f"Candidate: {candidate}")
    print(f"References:")
    for i, ref in enumerate(references, 1):
        print(f"  {i}. {ref}")
    print(f"\nMetrics:")
    print(f"  BLEU:      {result['bleu']:.4f}")
    print(f"  ROUGE-L:   {result['rouge']:.4f}")
    print(f"  Aggregate: {result['aggregate']:.4f}")

    # Example 3: Batch evaluation
    print("\n\n3. Batch Evaluation (simulating test run):")
    print("-" * 70)

    qa_pairs = [
        ("Paris is the capital of France.", "The capital of France is Paris."),
        ("London is the capital of England.", "The capital of England is London."),
        ("Berlin is the capital city of Germany.", "The capital of Germany is Berlin."),
    ]

    results = calculator.batch_evaluate(qa_pairs)

    print(f"\nEvaluated {len(qa_pairs)} QA pairs:")
    print(f"{'#':<3} {'BLEU':<8} {'ROUGE-L':<8} {'Aggregate':<10} {'Quality'}")
    print("-" * 70)

    for i, result in enumerate(results, 1):
        quality = "Excellent" if result['aggregate'] > 0.8 else \
                  "Good" if result['aggregate'] > 0.6 else \
                  "Fair" if result['aggregate'] > 0.4 else "Poor"

        print(f"{i:<3} {result['bleu']:<8.4f} {result['rouge']:<8.4f} "
              f"{result['aggregate']:<10.4f} {quality}")

    avg_aggregate = sum(r['aggregate'] for r in results) / len(results)
    print(f"\nAverage Aggregate Score: {avg_aggregate:.4f}")

    # Example 4: Quality assessment
    print("\n\n4. Quality Assessment:")
    print("-" * 70)

    test_cases = [
        ("Excellent answer", "The quick brown fox.", "The quick brown fox."),
        ("Good answer", "The quick brown fox jumps.", "The quick brown fox."),
        ("Hallucinated", "The quick brown fox jumps over the lazy dog and runs away.", "The quick brown fox."),
        ("Wrong answer", "The slow red cat.", "The quick brown fox."),
    ]

    print(f"\n{'Case':<20} {'BLEU':<8} {'ROUGE':<8} {'C-F1':<8} {'Assessment'}")
    print("-" * 70)

    for case_name, candidate, ground_truth in test_cases:
        result = calculator.evaluate_answer(candidate, ground_truth)

        # Assess quality
        if result['aggregate'] > 0.9:
            assessment = "Excellent"
        elif result['aggregate'] > 0.7:
            assessment = "Good"
        elif result['aggregate'] > 0.5:
            assessment = "Acceptable"
        elif result['aggregate'] > 0.3:
            assessment = "Poor"
        else:
            assessment = "Very Poor"

        # Check for hallucination
        if result['content_f1'] < 0.6 and result['rouge'] > 0.4:
            assessment += " (Verbose)"

        print(f"{case_name:<20} {result['bleu']:<8.4f} {result['rouge']:<8.4f} "
              f"{result['content_f1']:<8.4f} {assessment}")

    print("\n" + "=" * 70)
    print("Integration example completed!")
    print("=" * 70)


def integration_with_eval_repo():
    """
    Example of how to integrate with the eval repository.

    This shows how you might modify eval_repo.py to automatically
    calculate metrics when storing evaluation results.
    """
    print("\n\nIntegration with EvalRepo:")
    print("=" * 70)
    print("""
# In your evaluation pipeline (e.g., when running a test):

from metrics.integration_example import EvalMetricsCalculator

calculator = EvalMetricsCalculator()

# When you have an LLM answer and ground truth
llm_answer = "Generated answer from your RAG system"
ground_truth = "Expected answer from QA pair"

# Calculate metrics
metrics = calculator.evaluate_answer(llm_answer, ground_truth)

# Store in database via eval_repo
eval_data = {
    "test_run_id": test_run_id,
    "qa_pair_id": qa_pair_id,
    "answer": llm_answer,
    "bleu": metrics["bleu"],
    "rouge": metrics["rouge"],
    # ... other fields
}

# Insert into database
eval_repo.insert(eval_data)
    """)
    print("=" * 70)


if __name__ == "__main__":
    example_usage()
    integration_with_eval_repo()
