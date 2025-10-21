"""
Test suite for Groq provider routing in ModelFactory.

This test ensures that various model name formats for OSS models
correctly route to the Groq provider.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm.model_factory import ModelFactory, get_llm
from llm.groq_llm import GroqLLM
from llm.groq_provider import GroqProvider
from llm.openai_llm import OpenAILLM


class TestGroqProviderRouting:
    """Test cases for Groq provider routing."""

    @pytest.fixture
    def mock_factory(self):
        """Create a ModelFactory with mocked providers."""
        with patch('llm.model_factory.os.getenv') as mock_env:
            # Mock environment variables
            mock_env.side_effect = lambda key: {
                'OPENAI_API_KEY': 'test_openai_key',
                'GROQ_API_KEY': 'test_groq_key'
            }.get(key)

            factory = ModelFactory(api_key='test_openai_key', groq_api_key='test_groq_key')
            return factory

    @pytest.fixture
    def mock_groq_provider(self):
        """Create a mocked Groq provider."""
        with patch('llm.groq_provider.GroqProvider') as mock_provider_class:
            mock_provider = Mock(spec=GroqProvider)
            mock_llm = Mock(spec=GroqLLM)
            mock_llm.get_model_name.return_value = 'groq_gpt_oss_120b'
            mock_provider.get_llm.return_value = mock_llm
            mock_provider_class.return_value = mock_provider
            return mock_provider

    def test_groq_gpt_oss_120b_with_prefix(self, mock_factory):
        """Test that 'groq_gpt_oss_120b' routes to Groq provider."""
        with patch.object(mock_factory._groq_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=GroqLLM)
            mock_get_llm.return_value = mock_llm

            llm = mock_factory.get_llm('groq_gpt_oss_120b')

            # Verify Groq provider was called with correct model name
            mock_get_llm.assert_called_once_with('groq_gpt_oss_120b')
            assert llm == mock_llm

    def test_oss_120b_without_prefix(self, mock_factory):
        """Test that 'oss-120b' or 'oss_120b' routes to Groq provider."""
        with patch.object(mock_factory._groq_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=GroqLLM)
            mock_get_llm.return_value = mock_llm

            # Test with hyphen
            llm = mock_factory.get_llm('oss-120b')
            mock_get_llm.assert_called_with('groq_gpt_oss_120b')
            assert llm == mock_llm

            mock_get_llm.reset_mock()

            # Test with underscore
            llm = mock_factory.get_llm('oss_120b')
            mock_get_llm.assert_called_with('groq_gpt_oss_120b')
            assert llm == mock_llm

    def test_gpt_oss_120b_without_groq_prefix(self, mock_factory):
        """Test that 'gpt-oss-120b' routes to Groq provider."""
        with patch.object(mock_factory._groq_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=GroqLLM)
            mock_get_llm.return_value = mock_llm

            llm = mock_factory.get_llm('gpt-oss-120b')

            # Should normalize to groq_gpt_oss_120b
            mock_get_llm.assert_called_once_with('groq_gpt_oss_120b')
            assert llm == mock_llm

    def test_oss_20b_routes_to_groq(self, mock_factory):
        """Test that 'oss-20b' variants route to Groq provider."""
        with patch.object(mock_factory._groq_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=GroqLLM)
            mock_get_llm.return_value = mock_llm

            # Test oss-20b
            llm = mock_factory.get_llm('oss-20b')
            mock_get_llm.assert_called_with('groq_gpt_oss_20b')
            assert llm == mock_llm

            mock_get_llm.reset_mock()

            # Test with full name
            llm = mock_factory.get_llm('groq_gpt_oss_20b')
            mock_get_llm.assert_called_with('groq_gpt_oss_20b')
            assert llm == mock_llm

    def test_case_insensitive_routing(self, mock_factory):
        """Test that model names are case-insensitive."""
        with patch.object(mock_factory._groq_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=GroqLLM)
            mock_get_llm.return_value = mock_llm

            # Test uppercase
            llm = mock_factory.get_llm('OSS-120B')
            mock_get_llm.assert_called_with('groq_gpt_oss_120b')

            mock_get_llm.reset_mock()

            # Test mixed case
            llm = mock_factory.get_llm('Groq_GPT_OSS_120B')
            mock_get_llm.assert_called_with('groq_gpt_oss_120b')

    def test_openai_models_not_affected(self, mock_factory):
        """Test that OpenAI model routing is not affected by changes."""
        with patch.object(mock_factory._openai_provider, 'get_llm') as mock_get_llm:
            mock_llm = Mock(spec=OpenAILLM)
            mock_get_llm.return_value = mock_llm

            # Test OpenAI 4o
            llm = mock_factory.get_llm('openai_4o')
            mock_get_llm.assert_called_once_with('openai_4o')
            assert llm == mock_llm

    def test_unsupported_model_raises_error(self, mock_factory):
        """Test that unsupported model names raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported LLM model"):
            mock_factory.get_llm('unsupported_model')

    def test_convenience_function_get_llm(self):
        """Test the global get_llm convenience function."""
        with patch('llm.model_factory.get_model_factory') as mock_get_factory:
            mock_factory = Mock(spec=ModelFactory)
            mock_llm = Mock(spec=GroqLLM)
            mock_factory.get_llm.return_value = mock_llm
            mock_get_factory.return_value = mock_factory

            llm = get_llm('oss-120b')

            mock_factory.get_llm.assert_called_once_with('oss-120b')
            assert llm == mock_llm


class TestGroqLLMInitialization:
    """Test cases for GroqLLM initialization with different model names."""

    def test_groq_llm_accepts_correct_model_name(self):
        """Test that GroqLLM accepts 'groq_gpt_oss_120b' model name."""
        with patch('llm.groq_llm.AsyncGroq'):
            with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
                llm = GroqLLM(api_key='test_key', model_name='groq_gpt_oss_120b')
                assert llm.get_model_name() == 'groq_gpt_oss_120b'
                assert llm.config['model_name'] == 'openai/gpt-oss-120b'

    def test_groq_llm_rejects_invalid_model_name(self):
        """Test that GroqLLM rejects invalid model names."""
        with pytest.raises(ValueError, match="Unsupported model"):
            GroqLLM(api_key='test_key', model_name='invalid_model')


class TestIntegrationWithActualProviders:
    """Integration tests with actual provider instances (requires API keys)."""

    @pytest.mark.integration
    def test_factory_returns_groq_llm_instance(self):
        """Integration test: verify factory returns actual GroqLLM instance."""
        try:
            factory = ModelFactory()
            llm = factory.get_llm('oss-120b')

            # Verify it's a GroqLLM instance
            assert isinstance(llm, GroqLLM)
            assert llm.get_model_name() == 'groq_gpt_oss_120b'
            assert llm.config['model_name'] == 'openai/gpt-oss-120b'
        except ValueError as e:
            # Skip if API keys are not configured
            if "API key" in str(e):
                pytest.skip("GROQ_API_KEY not configured")
            raise

    @pytest.mark.integration
    def test_factory_returns_correct_provider_for_all_variants(self):
        """Integration test: verify all OSS model variants return GroqLLM."""
        variants = [
            'oss-120b',
            'oss_120b',
            'OSS-120B',
            'gpt-oss-120b',
            'groq_gpt_oss_120b',
            'GROQ_GPT_OSS_120B'
        ]

        try:
            factory = ModelFactory()
            for variant in variants:
                llm = factory.get_llm(variant)
                assert isinstance(llm, GroqLLM), f"Failed for variant: {variant}"
                assert llm.get_model_name() == 'groq_gpt_oss_120b'
        except ValueError as e:
            if "API key" in str(e):
                pytest.skip("GROQ_API_KEY not configured")
            raise


class TestModelNameNormalization:
    """Test cases for model name normalization logic."""

    @pytest.fixture
    def factory(self):
        """Create factory with test API keys."""
        return ModelFactory(api_key='test_openai_key', groq_api_key='test_groq_key')

    @pytest.mark.parametrize("input_name,expected_provider", [
        ('oss-120b', 'groq'),
        ('oss_120b', 'groq'),
        ('OSS-120B', 'groq'),
        ('gpt-oss-120b', 'groq'),
        ('GPT-OSS-120B', 'groq'),
        ('groq_gpt_oss_120b', 'groq'),
        ('GROQ_GPT_OSS_120B', 'groq'),
        ('oss-20b', 'groq'),
        ('groq_gpt_oss_20b', 'groq'),
        ('openai_4o', 'openai'),
        ('OpenAI_4O', 'openai'),
        ('openai_4o_mini', 'openai'),
    ])
    def test_model_name_routes_to_correct_provider(self, factory, input_name, expected_provider):
        """Test that various model names route to the correct provider."""
        if expected_provider == 'groq':
            with patch.object(factory._groq_provider, 'get_llm') as mock_groq:
                mock_groq.return_value = Mock(spec=GroqLLM)
                factory.get_llm(input_name)
                assert mock_groq.called, f"{input_name} should route to Groq"
        elif expected_provider == 'openai':
            with patch.object(factory._openai_provider, 'get_llm') as mock_openai:
                mock_openai.return_value = Mock(spec=OpenAILLM)
                factory.get_llm(input_name)
                assert mock_openai.called, f"{input_name} should route to OpenAI"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
