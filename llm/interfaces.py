"""
Abstract interfaces for LLM and embedding models.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio


class LLMInterface(ABC):
    """Abstract interface for Large Language Models."""

    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text based on input messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional model-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier used in the database."""
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return the maximum number of tokens supported by this model."""
        pass


class EmbeddingInterface(ABC):
    """Abstract interface for embedding models."""

    @abstractmethod
    async def embed_text(self, text: str, **kwargs) -> List[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional model-specific parameters

        Returns:
            List of float values representing the text embedding
        """
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for
            **kwargs: Additional model-specific parameters

        Returns:
            List of embedding vectors, one for each input text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier used in the database."""
        pass

    @abstractmethod
    def get_embedding_dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        pass


class LLMProvider(ABC):
    """Abstract provider for LLM services."""

    @abstractmethod
    def get_llm(self, model_name: str) -> LLMInterface:
        """
        Get an LLM instance for the specified model.

        Args:
            model_name: Model identifier (e.g., 'openai_4o')

        Returns:
            LLM interface instance
        """
        pass

    @abstractmethod
    def list_available_models(self) -> List[str]:
        """Return list of available model names."""
        pass


class EmbeddingProvider(ABC):
    """Abstract provider for embedding services."""

    @abstractmethod
    def get_embedding_model(self, model_name: str) -> EmbeddingInterface:
        """
        Get an embedding model instance for the specified model.

        Args:
            model_name: Model identifier (e.g., 'openai_text_embedding_large_3')

        Returns:
            Embedding interface instance
        """
        pass

    @abstractmethod
    def list_available_models(self) -> List[str]:
        """Return list of available embedding model names."""
        pass
