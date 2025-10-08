"""
OpenAI embedding model implementation.
"""
import os
from typing import List
from openai import AsyncOpenAI
from .interfaces import EmbeddingInterface


class OpenAIEmbeddings(EmbeddingInterface):
    """OpenAI embedding model implementation."""

    # Model configurations matching database defaults
    MODEL_CONFIGS = {
        'openai_text_embedding_large_3': {
            'dimensions': 3072,
            'model_name': 'text-embedding-3-large'
        },
        'openai_text_embedding_small_3': {
            'dimensions': 1536,
            'model_name': 'text-embedding-3-small'
        },
        'openai_text_embedding_ada_002': {
            'dimensions': 1536,
            'model_name': 'text-embedding-ada-002'
        }
    }

    def __init__(self, api_key: str = None, model_name: str = 'openai_text_embedding_large_3'):
        """
        Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: Model identifier from database (e.g., 'openai_text_embedding_large_3')
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model_name}. Available: {list(self.MODEL_CONFIGS.keys())}")

        self.model_name = model_name
        self.config = self.MODEL_CONFIGS[model_name]
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def embed_text(self, text: str, **kwargs) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to generate embedding for
            **kwargs: Additional parameters

        Returns:
            List of float values representing the text embedding
        """
        embeddings = await self.embed_texts([text], **kwargs)
        return embeddings[0]

    async def embed_texts(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors, one for each input text
        """
        try:
            # Filter out empty texts
            filtered_texts = [text for text in texts if text.strip()]

            if not filtered_texts:
                return [[] for _ in texts]

            response = await self.client.embeddings.create(
                model=self.config['model_name'],
                input=filtered_texts,
                **kwargs
            )

            # Create embeddings list matching original input order
            embeddings = []
            emb_idx = 0

            for original_text in texts:
                if original_text.strip():
                    embeddings.append(response.data[emb_idx].embedding)
                    emb_idx += 1
                else:
                    # Return zero vector for empty texts
                    embeddings.append([0.0] * self.config['dimensions'])

            return embeddings

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    def get_model_name(self) -> str:
        """Return the model identifier used in the database."""
        return self.model_name

    def get_embedding_dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        return self.config['dimensions']
