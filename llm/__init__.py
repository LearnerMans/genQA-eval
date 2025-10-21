# LLM interfaces package

from .interfaces import (
    LLMInterface,
    EmbeddingInterface,
    LLMProvider,
    EmbeddingProvider
)
from .openai_llm import OpenAILLM
from .openai_embeddings import OpenAIEmbeddings
from .openai_provider import OpenAIProvider
from .groq_llm import GroqLLM
from .groq_provider import GroqProvider
from .model_factory import (
    ModelFactory,
    get_model_factory,
    get_llm,
    get_embedding_model
)
from .prompting import (
    format_chunks,
    render_prompt_text,
    build_messages_for_prompt,
    answer_query_from_chunks,
)

__all__ = [
    # Interfaces
    'LLMInterface',
    'EmbeddingInterface',
    'LLMProvider',
    'EmbeddingProvider',

    # OpenAI implementations
    'OpenAILLM',
    'OpenAIEmbeddings',
    'OpenAIProvider',

    # Groq implementations
    'GroqLLM',
    'GroqProvider',

    # Factory and convenience functions
    'ModelFactory',
    'get_model_factory',
    'get_llm',
    'get_embedding_model',

    # Prompting utilities
    'format_chunks',
    'render_prompt_text',
    'build_messages_for_prompt',
    'answer_query_from_chunks',
]
