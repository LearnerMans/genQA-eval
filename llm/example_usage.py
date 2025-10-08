"""
Example usage of the LLM interfaces package.
"""
import asyncio
import os
from llm import get_llm, get_embedding_model, ModelFactory


async def example_usage():
    """Example of how to use the LLM interfaces."""

    # Set your OpenAI API key
    # os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

    # Using convenience functions
    try:
        # Get an LLM instance (uses default model from database)
        llm = get_llm('openai_4o')

        # Generate text
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]

        response = await llm.generate(messages)
        print(f"LLM Response: {response}")

        # Get an embedding model instance (uses default model from database)
        embedding_model = get_embedding_model('openai_text_embedding_large_3')

        # Generate embeddings
        texts = ["Hello world", "How are you?", "This is a test"]
        embeddings = await embedding_model.embed_texts(texts)

        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimensions: {embedding_model.get_embedding_dimensions()}")
        print(f"First embedding (first 5 values): {embeddings[0][:5]}")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except RuntimeError as e:
        print(f"API error: {e}")


async def example_factory():
    """Example using the ModelFactory directly."""

    # Create factory with custom API key
    factory = ModelFactory(api_key=os.getenv('OPENAI_API_KEY'))

    # List available models
    print("Available LLMs:", factory.list_available_llms())
    print("Available embedding models:", factory.list_available_embedding_models())

    # Check if models are supported
    print("openai_4o supported:", factory.is_llm_supported('openai_4o'))
    print("openai_text_embedding_large_3 supported:", factory.is_embedding_model_supported('openai_text_embedding_large_3'))


if __name__ == "__main__":
    print("=== LLM Interfaces Package Example ===")

    # Run examples
    asyncio.run(example_usage())
    print()
    asyncio.run(example_factory())
