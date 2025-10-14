"""
Quick example of RAG evaluation with GPT-5.

This script demonstrates how to use the RAG evaluator in your project.
API key will be automatically loaded from .env file.
"""

from metrics import evaluate_rag, format_evaluation_report
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env file!")
        print("\nPlease create a .env file in the project root with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        print("\nSee .env.example for an example.")
        return

    print("RAG Evaluation Example with GPT-5")
    print("=" * 80)

    # Example RAG system output
    query = "What are the symptoms of type 2 diabetes?"

    contexts = [
        "Type 2 diabetes symptoms include increased thirst, frequent urination, "
        "increased hunger, unintended weight loss, fatigue, blurred vision, "
        "slow-healing sores, and frequent infections.",

        "Type 2 diabetes often develops slowly. Some people have no noticeable "
        "symptoms initially.",

        "Regular blood sugar monitoring is important for diabetes management "
        "and preventing complications."
    ]

    answer = (
        "Common symptoms of type 2 diabetes include increased thirst, "
        "frequent urination, fatigue, and blurred vision. Some people may "
        "also experience weight loss and slow-healing wounds."
    )

    print(f"\nQuery: {query}")
    print(f"\nNumber of contexts: {len(contexts)}")
    print(f"Answer length: {len(answer)} characters")
    print("\nEvaluating with GPT-5...")
    print("-" * 80)

    # Evaluate using GPT-5
    result = evaluate_rag(
        query=query,
        contexts=contexts,
        answer=answer,
        model="gpt-5",  # Use GPT-5 for evaluation
        temperature=0.0  # Deterministic evaluation
    )

    # Print formatted report
    print(format_evaluation_report(result))

    # Access individual components
    print("\n" + "=" * 80)
    print("DETAILED BREAKDOWN")
    print("=" * 80)

    print(f"\nContext Relevance:")
    print(f"  Score: {result.context_relevance.score.value}")
    print(f"  Explanation: {result.context_relevance.explanation[:200]}...")

    print(f"\nGroundedness:")
    print(f"  Score: {result.groundedness.score.value}")
    print(f"  Claims: {result.groundedness.supported_claims}/{result.groundedness.total_claims} supported")
    print(f"  Explanation: {result.groundedness.explanation[:200]}...")

    print(f"\nAnswer Relevance:")
    print(f"  Score: {result.answer_relevance.score.value}")
    print(f"  Explanation: {result.answer_relevance.explanation[:200]}...")

    print("\n" + "=" * 80)
    print(f"Final Overall Score: {result.overall_score:.2f}/3.0")
    print("=" * 80)


if __name__ == "__main__":
    main()
