"""
Groq LLM implementation for GPT-OSS models with retry mechanism.
"""
import os
from typing import List, Dict, Any
from groq import AsyncGroq
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
                            f"Groq request failed with status {response.status_code}. "
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
                        f"Groq request failed with {type(e).__name__}. "
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


class GroqLLM(LLMInterface):
    """Groq LLM implementation for GPT-OSS models."""

    # Model configurations for Groq GPT-OSS models
    MODEL_CONFIGS = {
        'groq_gpt_oss_120b': {
            'max_tokens': 8192,
            'model_name': 'openai/gpt-oss-120b'
        },
        'groq_gpt_oss_20b': {
            'max_tokens': 8192,
            'model_name': 'openai/gpt-oss-20b'
        }
    }

    def __init__(self, api_key: str = None, model_name: str = 'groq_gpt_oss_120b'):
        """
        Initialize Groq LLM with retry mechanism.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model_name: Model identifier from database (e.g., 'groq_gpt_oss_120b')

        Retry Strategy:
            - Max retries: 3
            - Progressive backoff: 5s, 20s, 70s (1min 10sec)
            - Retries on: Rate limits, timeouts, connection errors, server errors
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key must be provided or set in GROQ_API_KEY environment variable")

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

        self.client = AsyncGroq(
            api_key=self.api_key,
            http_client=http_client,
            max_retries=0,  # Disable default retry, use our custom transport
            timeout=300.0   # 5 minute timeout
        )

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate text using Groq API.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional parameters (temperature, max_tokens, top_p, etc.)

        Returns:
            Generated text response
        """
        try:
            # Extract parameters with defaults
            max_tokens = kwargs.pop('max_tokens', self.config['max_tokens'])
            temperature = kwargs.pop('temperature', 0.2)
            top_p = kwargs.pop('top_p', 1.0)

            # Build the API call parameters
            api_params = {
                'model': self.config['model_name'],
                'messages': messages,
                'temperature': temperature,
                'top_p': top_p,
                'max_tokens': max_tokens,
            }

            # Add any additional kwargs that Groq supports
            if 'stop' in kwargs:
                api_params['stop'] = kwargs.pop('stop')

            # Pass any remaining kwargs
            api_params.update(kwargs)

            response = await self.client.chat.completions.create(**api_params)

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}") from e

    def get_model_name(self) -> str:
        """Return the model identifier used in the database."""
        return self.model_name

    def get_max_tokens(self) -> int:
        """Return the maximum number of tokens supported by this model."""
        return self.config['max_tokens']
