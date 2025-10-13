# LLM Interfaces Package

This package provides abstract interfaces and implementations for Large Language Models (LLMs) and embedding models, with a focus on compatibility with the RAG evaluation system database schema.

## Features

- **Abstract Interfaces**: Clean separation between interface definitions and implementations
- **OpenAI Integration**: Full support for OpenAI's GPT models and embedding models
- **Database Compatibility**: Model names match the database schema defaults
- **Async Support**: All operations are async for better performance
- **Factory Pattern**: Easy model instantiation with support for multiple providers
- **Extensible Design**: Easy to add new model providers

## Installation

The package requires the `openai` dependency, which is already included in the project's `pyproject.toml`.

## Quick Start

### Basic Usage

```python
import asyncio
import os
from llm import get_llm, get_embedding_model

# Set your OpenAI API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

async def main():
    # Get LLM instance using database model name
    llm = get_llm('openai_4o')

    # Generate text
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]

    response = await llm.generate(messages)
    print(response)

    # Get embedding model instance
    embedding_model = get_embedding_model('openai_text_embedding_large_3')

    # Generate embeddings
    texts = ["Hello world", "How are you?"]
    embeddings = await embedding_model.embed_texts(texts)

    print(f"Embedding dimensions: {embedding_model.get_embedding_dimensions()}")

asyncio.run(main())
```

### Prompting Helpers

Use the prompting utilities to render a prompt that contains the required placeholders `{{chunks}}` and `{{query}}`, then generate an answer from retrieved chunks.

```python
import asyncio
from llm import answer_query_from_chunks

prompt_template = (
    "You are a RAG assistant.\n\n"
    "Context:\n{{chunks}}\n\n"
    "Question: {{query}}\n"
    "Answer concisely based only on the context."
)

chunks = [
    "Python 3.12 introduced improvements to ...",
    "FastAPI is a modern, fast web framework ...",
]
query = "What is FastAPI?"

async def main():
    answer = await answer_query_from_chunks(
        llm='openai_4o',               # or pass an LLMInterface instance
        prompt_template=prompt_template,
        chunks=chunks,
        query=query,
        temperature=0.2,
        max_tokens=300,
    )
    print(answer)

asyncio.run(main())
```

### Using the Factory

```python
from llm import ModelFactory

# Create factory instance
factory = ModelFactory(api_key='your-api-key')

# List available models
print("LLMs:", factory.list_available_llms())
print("Embeddings:", factory.list_available_embedding_models())

# Get specific models
llm = factory.get_llm('openai_4o')
embedding_model = factory.get_embedding_model('openai_text_embedding_large_3')
```

## Supported Models

### LLM Models

The following OpenAI models are supported, matching the database defaults:

- `openai_4o` → GPT-4o (default)
- `openai_4o_mini` → GPT-4o Mini
- `openai_4` → GPT-4
- `openai_3_5_turbo` → GPT-3.5 Turbo

### Embedding Models

The following OpenAI embedding models are supported:

- `openai_text_embedding_large_3` → text-embedding-3-large (3072 dimensions, default)
- `openai_text_embedding_small_3` → text-embedding-3-small (1536 dimensions)
- `openai_text_embedding_ada_002` → text-embedding-ada-002 (1536 dimensions)

## Architecture

### Core Interfaces

- `LLMInterface`: Abstract base class for language models
- `EmbeddingInterface`: Abstract base class for embedding models
- `LLMProvider`: Abstract provider for LLM services
- `EmbeddingProvider`: Abstract provider for embedding services

### Implementations

- `OpenAILLM`: OpenAI GPT model implementation
- `OpenAIEmbeddings`: OpenAI embedding model implementation
- `OpenAIProvider`: Provider for both OpenAI LLMs and embeddings

### Factory

- `ModelFactory`: Factory class for creating model instances
- Convenience functions: `get_llm()`, `get_embedding_model()`

## Configuration

### API Key

Set your OpenAI API key using one of these methods:

```python
# Method 1: Environment variable (recommended)
import os
os.environ['OPENAI_API_KEY'] = 'your-api-key'

# Method 2: Pass directly to factory
factory = ModelFactory(api_key='your-api-key')

# Method 3: Pass directly to model instances
llm = OpenAILLM(api_key='your-api-key', model_name='openai_4o')
```

### Model Selection

Models are identified using the names from the database schema:

```python
# For generative models (config.generative_model)
llm = get_llm('openai_4o')  # Default from database

# For embedding models (config.embedding_model)
embedding_model = get_embedding_model('openai_text_embedding_large_3')  # Default from database
```

## Error Handling

The package raises specific exceptions:

- `ValueError`: For unsupported models or missing API keys
- `RuntimeError`: For API errors (network issues, quota exceeded, etc.)

```python
try:
    llm = get_llm('unsupported_model')
except ValueError as e:
    print(f"Model not supported: {e}")

try:
    response = await llm.generate(messages)
except RuntimeError as e:
    print(f"API error: {e}")
```

## Integration with RAG System

This package is designed to work seamlessly with the RAG evaluation system:

1. Model names match the database schema defaults
2. Async operations integrate well with FastAPI
3. Factory pattern allows easy model switching based on configuration
4. Error handling is compatible with the existing error handling patterns

## Example Integration

```python
from llm import get_llm, get_embedding_model
from db.db import DB

async def process_with_config(config):
    """Process using models from database configuration."""

    # Get models based on config
    llm = get_llm(config['generative_model'])
    embedding_model = get_embedding_model(config['embedding_model'])

    # Use models for your RAG operations
    response = await llm.generate([
        {"role": "user", "content": "Generate response based on context"}
    ])

    embeddings = await embedding_model.embed_texts(text_chunks)

    return response, embeddings
```

## Extending the Package

To add support for other model providers:

1. Implement the `LLMInterface` and/or `EmbeddingInterface`
2. Create provider classes implementing `LLMProvider` and/or `EmbeddingProvider`
3. Update the `ModelFactory` to handle the new provider
4. Add model name mappings that match your database schema

This design makes it easy to extend the package with support for Anthropic, Google, or other model providers while maintaining compatibility with the existing RAG evaluation system.
