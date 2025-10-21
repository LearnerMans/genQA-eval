"""
Groq provider implementation.
"""
from typing import List
from .interfaces import LLMProvider
from .groq_llm import GroqLLM


class GroqProvider(LLMProvider):
    """Provider for Groq models."""

    def __init__(self, api_key: str = None):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key

    def get_llm(self, model_name: str) -> GroqLLM:
        """
        Get a Groq LLM instance.

        Args:
            model_name: Model identifier (e.g., 'groq_gpt_oss_120b')

        Returns:
            Groq LLM instance
        """
        return GroqLLM(api_key=self.api_key, model_name=model_name)

    def list_available_models(self) -> List[str]:
        """Return list of available Groq LLM model names."""
        return list(GroqLLM.MODEL_CONFIGS.keys())
