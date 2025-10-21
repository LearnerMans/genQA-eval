"""
OpenAI embedding model implementation with retry mechanism.
"""
import os
from typing import List
from openai import AsyncOpenAI
from .interfaces import EmbeddingInterface
import httpx
from httpx import Response, Request
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)


class CustomRetryTransport(httpx.AsyncHTTPTransport):
    """Custom HTTP transport with progressive retry backoff."""

    # Progressive backoff times: 5s, 20s, 70s (3 retries total)
    BACKOFF_TIMES = [5.0, 20.0, 70.0]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retry_count = {}  # Track retries per request

    async def handle_async_request(self, request: Request) -> Response:
        """Handle request with custom retry logic."""
        request_id = id(request)
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                response = await super().handle_async_request(request)

                # Retry on rate limit (429) or server errors (500+)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < max_retries:
                        backoff_time = self.BACKOFF_TIMES[attempt]
                        logger.warning(
                            f"Embedding request failed with status {response.status_code}. "
                            f"Retry {attempt + 1}/{max_retries} after {backoff_time}s"
                        )
                        await asyncio.sleep(backoff_time)
                        continue

                # Success or non-retryable error
                return response

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
                if attempt < max_retries:
                    backoff_time = self.BACKOFF_TIMES[attempt]
                    logger.warning(
                        f"Embedding request failed with {type(e).__name__}. "
                        f"Retry {attempt + 1}/{max_retries} after {backoff_time}s"
                    )
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    raise

            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error: {type(e).__name__}: {str(e)}")
                raise

        # This should not be reached, but just in case
        return response


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
        Initialize OpenAI embeddings with retry mechanism.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: Model identifier from database (e.g., 'openai_text_embedding_large_3')

        Retry Strategy:
            - Max retries: 3
            - Progressive backoff: 5s, 20s, 70s (1min 10sec)
            - Retries on: Rate limits, timeouts, connection errors, server errors
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model_name}. Available: {list(self.MODEL_CONFIGS.keys())}")

        self.model_name = model_name
        self.config = self.MODEL_CONFIGS[model_name]

        # Configure HTTP client with custom retry transport
        # Progressive backoff: 5s, 20s, 70s (total 3 retries)
        transport = CustomRetryTransport()
        http_client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(300.0, connect=60.0),  # 5 min total, 60s connect
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100)
        )

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            http_client=http_client,
            max_retries=0,  # Disable default retry, use our custom transport
            timeout=300.0   # 5 minute timeout
        )

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
