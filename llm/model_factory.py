"""
Factory for creating LLM and embedding model instances.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from .interfaces import LLMInterface, EmbeddingInterface
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider

# Load environment variables from .env file
load_dotenv()


class ModelFactory:
    """Factory for creating model instances based on database model names."""

    def __init__(self, api_key: str = None, groq_api_key: str = None):
        """
        Initialize model factory.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            groq_api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        self._openai_provider = OpenAIProvider(api_key=self.api_key)
        self._groq_provider = GroqProvider(api_key=self.groq_api_key)
        self._embedding_provider = self._openai_provider  # OpenAI provider handles embeddings

    def get_llm(self, model_name: str) -> LLMInterface:
        """
        Get an LLM instance for the specified model name.

        Args:
            model_name: Model identifier from database (e.g., 'openai_4o', 'groq_gpt_oss_120b')

        Returns:
            LLM interface instance

        Raises:
            ValueError: If model name is not supported
        """
        # Normalize model name - handle variations of oss-120b
        normalized_name = model_name.lower().replace('-', '_')

        # Special handling for oss models - route to Groq
        if 'oss_120b' in normalized_name or 'oss_20b' in normalized_name:
            # Ensure proper groq_ prefix
            if not normalized_name.startswith('groq_'):
                if 'oss_120b' in normalized_name:
                    normalized_name = 'groq_gpt_oss_120b'
                elif 'oss_20b' in normalized_name:
                    normalized_name = 'groq_gpt_oss_20b'
            return self._groq_provider.get_llm(normalized_name)

        if normalized_name.startswith('openai_'):
            return self._openai_provider.get_llm(normalized_name)
        elif normalized_name.startswith('groq_'):
            return self._groq_provider.get_llm(normalized_name)
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
        openai_models = self._openai_provider.list_available_models()
        groq_models = self._groq_provider.list_available_models()
        return openai_models + groq_models

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
