"""
Test script for RAG evaluator using GPT-5.

This script tests the RAG evaluation functionality with sample data.
API key will be automatically loaded from .env file.
"""

import os
from dotenv import load_dotenv
from rag_evaluator import evaluate_rag, format_evaluation_report

# Load environment variables from .env file
load_dotenv()


def test_basic_evaluation():
    """Test basic RAG evaluation with a medical query example."""
    print("Testing RAG Evaluator with GPT-5...")
    print("=" * 80)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file in the project root with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        return

    # Test case 1: Medical query
    print("\nTest Case 1: Medical Query Evaluation")
    print("-" * 80)

    result = evaluate_rag(
        query="What are the symptoms of type 2 diabetes?",
        contexts=[
            "Type 2 diabetes symptoms include increased thirst, frequent urination, increased hunger, unintended weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections.",
            "Type 2 diabetes often develops slowly. Some people have no noticeable symptoms initially.",
            "Regular blood sugar monitoring is important for diabetes management and preventing complications."
        ],
        answer="Common symptoms of type 2 diabetes include increased thirst, frequent urination, fatigue, and blurred vision. Some people may also experience weight loss and slow-healing wounds."
    )

    print(format_evaluation_report(result))

    # Test case 2: Technical query with hallucination
    print("\n\nTest Case 2: Technical Query with Potential Hallucination")
    print("-" * 80)

    result2 = evaluate_rag(
        query="What is the capital of France?",
        contexts=[
            "Paris is the capital and most populous city of France.",
            "France is a country located in Western Europe."
        ],
        answer="The capital of France is Paris. It is also the largest city in Europe by population."  # Hallucination about largest city
    )

    print(format_evaluation_report(result2))

    # Test case 3: Irrelevant context
    print("\n\nTest Case 3: Query with Irrelevant Context")
    print("-" * 80)

    result3 = evaluate_rag(
        query="How do I install Python?",
        contexts=[
            "JavaScript is a programming language commonly used for web development.",
            "The weather in San Francisco is typically mild year-round.",
            "Python can be installed by downloading it from python.org and running the installer."
        ],
        answer="You can install Python by visiting python.org, downloading the installer for your operating system, and running it."
    )

    print(format_evaluation_report(result3))

    print("\n" + "=" * 80)
    print("All tests completed successfully!")


if __name__ == "__main__":
    test_basic_evaluation()
