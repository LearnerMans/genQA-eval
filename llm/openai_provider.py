"""
OpenAI provider implementation.
"""
from typing import List
from .interfaces import LLMProvider, EmbeddingProvider
from .openai_llm import OpenAILLM
from .openai_embeddings import OpenAIEmbeddings


class OpenAIProvider(LLMProvider, EmbeddingProvider):
    """Provider for OpenAI models."""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key

    def get_llm(self, model_name: str) -> OpenAILLM:
        """
        Get an OpenAI LLM instance.

        Args:
            model_name: Model identifier (e.g., 'openai_4o')

        Returns:
            OpenAI LLM instance
        """
        return OpenAILLM(api_key=self.api_key, model_name=model_name)

    def get_embedding_model(self, model_name: str) -> OpenAIEmbeddings:
        """
        Get an OpenAI embedding model instance.

        Args:
            model_name: Model identifier (e.g., 'openai_text_embedding_large_3')

        Returns:
            OpenAI embedding model instance
        """
        return OpenAIEmbeddings(api_key=self.api_key, model_name=model_name)

    def list_available_models(self) -> List[str]:
        """Return list of available OpenAI LLM model names."""
        return list(OpenAILLM.MODEL_CONFIGS.keys())

    def list_available_embedding_models(self) -> List[str]:
        """Return list of available OpenAI embedding model names."""
        return list(OpenAIEmbeddings.MODEL_CONFIGS.keys())
