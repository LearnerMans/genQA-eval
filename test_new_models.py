"""
Test script for GPT-4.1 and Groq OSS-120B models.
"""
import asyncio
import sys
from llm import get_llm, answer_query_from_chunks

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def test_gpt_4_1():
    """Test OpenAI GPT-4.1 model."""
    print("\n" + "="*60)
    print("Testing OpenAI GPT-4.1")
    print("="*60)

    try:
        llm = get_llm('openai_4_1')
        print(f"✓ Model initialized: {llm.get_model_name()}")
        print(f"✓ Max tokens: {llm.get_max_tokens()}")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from GPT-4.1!' and confirm you are working."}
        ]

        print("\nGenerating response...")
        response = await llm.generate(messages, temperature=0.2, max_tokens=100)
        print(f"✓ Response: {response}")
        print("\n✓ GPT-4.1 test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ GPT-4.1 test FAILED: {str(e)}")
        return False


async def test_groq_oss_120b():
    """Test Groq GPT-OSS-120B model."""
    print("\n" + "="*60)
    print("Testing Groq GPT-OSS-120B")
    print("="*60)

    try:
        llm = get_llm('groq_gpt_oss_120b')
        print(f"✓ Model initialized: {llm.get_model_name()}")
        print(f"✓ Max tokens: {llm.get_max_tokens()}")

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Groq OSS-120B!' and confirm you are working."}
        ]

        print("\nGenerating response...")
        response = await llm.generate(messages, temperature=0.2, max_tokens=100)
        print(f"✓ Response: {response}")
        print("\n✓ Groq OSS-120B test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Groq OSS-120B test FAILED: {str(e)}")
        return False


async def test_with_chunks():
    """Test answer_query_from_chunks with both models."""
    print("\n" + "="*60)
    print("Testing answer_query_from_chunks Integration")
    print("="*60)

    prompt_template = """Answer the following question based on the provided context.

Context:
{{chunks}}

Question: {{query}}

Answer:"""

    chunks = [
        "Python is a high-level programming language known for its simplicity and readability.",
        "Python supports multiple programming paradigms including procedural, object-oriented, and functional programming."
    ]

    query = "What is Python?"

    # Test with GPT-4.1
    print("\n--- Testing GPT-4.1 with chunks ---")
    try:
        answer = await answer_query_from_chunks(
            llm='openai_4_1',
            prompt_template=prompt_template,
            chunks=chunks,
            query=query,
            temperature=0.2,
            max_tokens=200
        )
        print(f"✓ Answer: {answer}")
        print("✓ GPT-4.1 chunk test PASSED")
    except Exception as e:
        print(f"✗ GPT-4.1 chunk test FAILED: {str(e)}")

    # Test with Groq OSS-120B
    print("\n--- Testing Groq OSS-120B with chunks ---")
    try:
        answer = await answer_query_from_chunks(
            llm='groq_gpt_oss_120b',
            prompt_template=prompt_template,
            chunks=chunks,
            query=query,
            temperature=0.2,
            max_tokens=200
        )
        print(f"✓ Answer: {answer}")
        print("✓ Groq OSS-120B chunk test PASSED")
    except Exception as e:
        print(f"✗ Groq OSS-120B chunk test FAILED: {str(e)}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("STARTING MODEL INTEGRATION TESTS")
    print("="*60)

    results = []

    # Test individual models
    results.append(("GPT-4.1", await test_gpt_4_1()))
    results.append(("Groq OSS-120B", await test_groq_oss_120b()))

    # Test with chunks
    await test_with_chunks()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for model_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{model_name}: {status}")

    print("\n" + "="*60)
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
