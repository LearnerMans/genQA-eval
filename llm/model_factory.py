"""
Factory for creating LLM and embedding model instances.
"""
import os
from typing import Optional
from .interfaces import LLMInterface, EmbeddingInterface
from .openai_provider import OpenAIProvider


class ModelFactory:
    """Factory for creating model instances based on database model names."""

    def __init__(self, api_key: str = None):
        """
        Initialize model factory.

        Args:
            api_key: API key for model providers (defaults to environment variables)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self._llm_provider = OpenAIProvider(api_key=self.api_key)
        self._embedding_provider = self._llm_provider  # OpenAI provider handles both

    def get_llm(self, model_name: str) -> LLMInterface:
        """
        Get an LLM instance for the specified model name.

        Args:
            model_name: Model identifier from database (e.g., 'openai_4o')

        Returns:
            LLM interface instance

        Raises:
            ValueError: If model name is not supported
        """
        if model_name.startswith('openai_'):
            return self._llm_provider.get_llm(model_name)
        else:
            raise ValueError(f"Unsupported LLM model: {model_name}")

    def get_embedding_model(self, model_name: str) -> EmbeddingInterface:
        """
        Get an embedding model instance for the specified model name.

        Args:
            model_name: Model identifier from database (e.g., 'openai_text_embedding_large_3')

        Returns:
            Embedding interface instance

        Raises:
            ValueError: If model name is not supported
        """
        if model_name.startswith('openai_'):
            return self._embedding_provider.get_embedding_model(model_name)
        else:
            raise ValueError(f"Unsupported embedding model: {model_name}")

    def list_available_llms(self) -> list[str]:
        """Return list of available LLM model names."""
        return self._llm_provider.list_available_models()

    def list_available_embedding_models(self) -> list[str]:
        """Return list of available embedding model names."""
        return self._embedding_provider.list_available_embedding_models()

    def is_llm_supported(self, model_name: str) -> bool:
        """Check if the given LLM model is supported."""
        return model_name in self.list_available_llms()

    def is_embedding_model_supported(self, model_name: str) -> bool:
        """Check if the given embedding model is supported."""
        return model_name in self.list_available_embedding_models()


# Global factory instance
_model_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """Get the global model factory instance."""
    global _model_factory
    if _model_factory is None:
        _model_factory = ModelFactory()
    return _model_factory


def get_llm(model_name: str) -> LLMInterface:
    """
    Convenience function to get an LLM instance.

    Args:
        model_name: Model identifier from database

    Returns:
        LLM interface instance
    """
    return get_model_factory().get_llm(model_name)


def get_embedding_model(model_name: str) -> EmbeddingInterface:
    """
    Convenience function to get an embedding model instance.

    Args:
        model_name: Model identifier from database

    Returns:
        Embedding interface instance
    """
    return get_model_factory().get_embedding_model(model_name)
