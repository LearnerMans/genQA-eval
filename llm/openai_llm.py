"""
OpenAI LLM implementation with retry mechanism.
"""
import os
from typing import List, Dict, Any
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from dotenv import load_dotenv
from .interfaces import LLMInterface
import httpx
from httpx import Response, Request
import asyncio
import logging

# Load environment variables from .env file
load_dotenv()

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
                            f"Request failed with status {response.status_code}. "
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
                        f"Request failed with {type(e).__name__}. "
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


class OpenAILLM(LLMInterface):
    """OpenAI LLM implementation."""

    # Model configurations matching database defaults
    MODEL_CONFIGS = {
        'openai_4o': {
            'max_tokens': 4096,
            'model_name': 'gpt-4o'
        },
        'openai_4o_mini': {
            'max_tokens': 4096,
            'model_name': 'gpt-4o-mini'
        },
        'openai_4': {
            'max_tokens': 4096,
            'model_name': 'gpt-4'
        },
        'openai_3_5_turbo': {
            'max_tokens': 4096,
            'model_name': 'gpt-3.5-turbo'
        },
        'openai_4_1': {
            'max_tokens': 16384,
            'model_name': 'gpt-4.1-2025-04-14'
        },
        'openai_4_1_mini': {
            'max_tokens': 16384,
            'model_name': 'gpt-4.1-mini-2025-04-14'
        },
        'openai_4_1_nano': {
            'max_tokens': 16384,
            'model_name': 'gpt-4.1-nano-2025-04-14'
        }
    }

    def __init__(self, api_key: str = None, model_name: str = 'openai_4o'):
        """
        Initialize OpenAI LLM with retry mechanism.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: Model identifier from database (e.g., 'openai_4o')

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

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text using OpenAI API.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        try:
            # Use provided max_tokens or default from config
            max_tokens = kwargs.pop('max_tokens', self.config['max_tokens'])
            temperature = kwargs.pop('temperature', 0.7)

            response = await self.client.chat.completions.create(
                model=self.config['model_name'],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    def get_model_name(self) -> str:
        """Return the model identifier used in the database."""
        return self.model_name

    def get_max_tokens(self) -> int:
        """Return the maximum number of tokens supported by this model."""
        return self.config['max_tokens']
