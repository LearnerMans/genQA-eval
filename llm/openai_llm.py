"""
OpenAI LLM implementation.
"""
import os
from typing import List, Dict, Any
from openai import AsyncOpenAI
from .interfaces import LLMInterface


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
        }
    }

    def __init__(self, api_key: str = None, model_name: str = 'openai_4o'):
        """
        Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: Model identifier from database (e.g., 'openai_4o')
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        if model_name not in self.MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model_name}. Available: {list(self.MODEL_CONFIGS.keys())}")

        self.model_name = model_name
        self.config = self.MODEL_CONFIGS[model_name]
        self.client = AsyncOpenAI(api_key=self.api_key)

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
            max_tokens = kwargs.get('max_tokens', self.config['max_tokens'])

            response = await self.client.chat.completions.create(
                model=self.config['model_name'],
                messages=messages,
                max_tokens=max_tokens,
                temperature=kwargs.get('temperature', 0.7),
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
