"""
Integration example: Using LLM-as-a-Judge with existing evaluation pipeline.

This shows how to integrate the GPT-5 RAG evaluator with your existing
test runs and evaluation repository.
"""

from typing import List, Dict, Any
from metrics import evaluate_rag, score_to_numeric


class LLMJudgeEvaluator:
    """
    Wrapper class for integrating LLM-as-a-Judge into your evaluation pipeline.
    """

    def __init__(self, model: str = "gpt-5", temperature: float = 0.0):
        """
        Initialize the LLM Judge evaluator.

        Args:
            model: GPT model to use (default: gpt-5)
            temperature: Temperature for evaluation (default: 0.0)
        """
        self.model = model
        self.temperature = temperature

    def evaluate_single(
        self,
        query: str,
        contexts: List[str],
        answer: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single RAG output.

        Args:
            query: User query
            contexts: Retrieved contexts
            answer: Generated answer

        Returns:
            Dictionary with scores and explanations
        """
        evaluation = evaluate_rag(
            query=query,
            contexts=contexts,
            answer=answer,
            model=self.model,
            temperature=self.temperature
        )

        return {
            "overall_score": evaluation.overall_score,
            "scores": {
                "context_relevance": score_to_numeric(evaluation.context_relevance.score),
                "groundedness": score_to_numeric(evaluation.groundedness.score),
                "answer_relevance": score_to_numeric(evaluation.answer_relevance.score)
            },
            "explanations": {
                "context_relevance": evaluation.context_relevance.explanation,
                "groundedness": evaluation.groundedness.explanation,
                "answer_relevance": evaluation.answer_relevance.explanation
            },
            "details": {
                "per_context_scores": evaluation.context_relevance.per_context_scores,
                "supported_claims": evaluation.groundedness.supported_claims,
                "total_claims": evaluation.groundedness.total_claims
            }
        }

    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple test cases.

        Args:
            test_cases: List of dicts with 'query', 'contexts', 'answer'

        Returns:
            List of evaluation results
        """
        results = []
        for i, test_case in enumerate(test_cases):
            print(f"Evaluating test case {i+1}/{len(test_cases)}...")
            result = self.evaluate_single(
                query=test_case["query"],
                contexts=test_case["contexts"],
                answer=test_case["answer"]
            )
            result["test_id"] = test_case.get("test_id", i)
            results.append(result)

        return results


# Example integration with your evaluation system
def integrate_with_eval_repo(run_id: int, test_id: int):
    """
    Example: Integrate with your existing evaluation repository.

    This function shows how you might integrate LLM-as-a-Judge
    with your existing database schema and evaluation handlers.
    """
    # Initialize evaluator
    evaluator = LLMJudgeEvaluator(model="gpt-5")

    # Fetch test data from your database
    # (Replace with actual database calls)
    test_data = {
        "query": "What are the benefits of exercise?",
        "contexts": [
            "Regular exercise improves cardiovascular health.",
            "Exercise helps maintain healthy weight.",
            "Physical activity reduces stress and anxiety."
        ],
        "answer": "Exercise has many benefits including better heart health and weight management."
    }

    # Evaluate using LLM Judge
    evaluation = evaluator.evaluate_single(
        query=test_data["query"],
        contexts=test_data["contexts"],
        answer=test_data["answer"]
    )

    # Store results in your database
    store_evaluation_results(
        run_id=run_id,
        test_id=test_id,
        evaluation_type="llm_judge_gpt5",
        overall_score=evaluation["overall_score"],
        metrics=evaluation["scores"],
        details=evaluation
    )

    return evaluation


def store_evaluation_results(
    run_id: int,
    test_id: int,
    evaluation_type: str,
    overall_score: float,
    metrics: Dict[str, float],
    details: Dict[str, Any]
):
    """
    Store evaluation results in your database.

    This is a placeholder - replace with your actual database logic.
    """
    # Example: Insert into your evaluations table
    print(f"Storing evaluation for run_id={run_id}, test_id={test_id}")
    print(f"Type: {evaluation_type}")
    print(f"Overall Score: {overall_score:.2f}/3.0")
    print(f"Metrics: {metrics}")

    # Your actual implementation might look like:
    """
    from repos.eval_repo import EvalRepo

    repo = EvalRepo()
    repo.store_llm_evaluation(
        run_id=run_id,
        test_id=test_id,
        evaluation_type=evaluation_type,
        overall_score=overall_score,
        context_relevance=metrics["context_relevance"],
        groundedness=metrics["groundedness"],
        answer_relevance=metrics["answer_relevance"],
        details_json=json.dumps(details)
    )
    """
    pass


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file in the project root with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        exit(1)

    # Example 1: Evaluate a single case
    print("Example 1: Single Evaluation")
    print("=" * 80)

    evaluator = LLMJudgeEvaluator(model="gpt-5")

    result = evaluator.evaluate_single(
        query="What is machine learning?",
        contexts=[
            "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "ML algorithms improve their performance with experience.",
            "Common ML tasks include classification, regression, and clustering."
        ],
        answer="Machine learning is a branch of AI where systems learn from data to improve their performance over time."
    )

    print(f"Overall Score: {result['overall_score']:.2f}/3.0")
    print(f"Context Relevance: {result['scores']['context_relevance']:.1f}")
    print(f"Groundedness: {result['scores']['groundedness']:.1f}")
    print(f"Answer Relevance: {result['scores']['answer_relevance']:.1f}")

    # Example 2: Batch evaluation
    print("\n\nExample 2: Batch Evaluation")
    print("=" * 80)

    test_cases = [
        {
            "test_id": 1,
            "query": "What is Python?",
            "contexts": ["Python is a high-level programming language.", "It's known for simplicity."],
            "answer": "Python is a popular programming language known for its simplicity."
        },
        {
            "test_id": 2,
            "query": "What causes rain?",
            "contexts": ["Rain forms when water vapor condenses.", "Precipitation occurs in clouds."],
            "answer": "Rain is caused by water vapor condensing in clouds and falling as precipitation."
        }
    ]

    batch_results = evaluator.evaluate_batch(test_cases)

    print(f"\nEvaluated {len(batch_results)} test cases:")
    for result in batch_results:
        print(f"  Test {result['test_id']}: Overall={result['overall_score']:.2f}/3.0")

    # Example 3: Integration with database
    print("\n\nExample 3: Database Integration")
    print("=" * 80)

    integrate_with_eval_repo(run_id=1, test_id=1)
