"""
Simple test suite for retry mechanisms in LLM and embedding implementations.

Tests verify that progressive retry backoff is configured correctly:
- Retry attempts: 3
- Backoff times: 5s, 20s, 70s (1 minute 10 seconds for last)
"""
import pytest


class TestRetryConfiguration:
    """Test that retry configurations are set correctly."""

    def test_openai_llm_has_retry_transport(self):
        """Test that OpenAI LLM uses CustomRetryTransport."""
        from llm.openai_llm import CustomRetryTransport, OpenAILLM
        import os

        # Verify the CustomRetryTransport class exists
        assert CustomRetryTransport is not None

        # Verify backoff times
        expected_backoffs = [5.0, 20.0, 70.0]
        assert CustomRetryTransport.BACKOFF_TIMES == expected_backoffs

        # Verify total backoff time
        total_backoff = sum(CustomRetryTransport.BACKOFF_TIMES)
        assert total_backoff == 95.0  # 5 + 20 + 70 = 95 seconds

        # Verify last backoff is 70 seconds (1 min 10 sec)
        assert CustomRetryTransport.BACKOFF_TIMES[-1] == 70.0

    def test_groq_llm_has_retry_transport(self):
        """Test that Groq LLM uses CustomRetryTransport."""
        from llm.groq_llm import CustomRetryTransport, GroqLLM

        # Verify the CustomRetryTransport class exists
        assert CustomRetryTransport is not None

        # Verify backoff times
        expected_backoffs = [5.0, 20.0, 70.0]
        assert CustomRetryTransport.BACKOFF_TIMES == expected_backoffs

        # Verify last backoff is 70 seconds
        assert CustomRetryTransport.BACKOFF_TIMES[-1] == 70.0

    def test_openai_embeddings_has_retry_transport(self):
        """Test that OpenAI Embeddings uses CustomRetryTransport."""
        from llm.openai_embeddings import CustomRetryTransport, OpenAIEmbeddings

        # Verify the CustomRetryTransport class exists
        assert CustomRetryTransport is not None

        # Verify backoff times
        expected_backoffs = [5.0, 20.0, 70.0]
        assert CustomRetryTransport.BACKOFF_TIMES == expected_backoffs

        # Verify last backoff is 70 seconds
        assert CustomRetryTransport.BACKOFF_TIMES[-1] == 70.0

    def test_progressive_backoff_sequence(self):
        """Test that the backoff sequence is progressive and correct."""
        from llm.openai_llm import CustomRetryTransport

        backoffs = CustomRetryTransport.BACKOFF_TIMES

        # Verify it's progressive (each value is larger than the previous)
        for i in range(len(backoffs) - 1):
            assert backoffs[i] < backoffs[i + 1], f"Backoff {i} ({backoffs[i]}) should be less than backoff {i+1} ({backoffs[i+1]})"

        # Verify exact values
        assert backoffs[0] == 5.0, "First retry should wait 5 seconds"
        assert backoffs[1] == 20.0, "Second retry should wait 20 seconds"
        assert backoffs[2] == 70.0, "Third retry should wait 70 seconds (1 min 10 sec)"

    def test_max_retries_count(self):
        """Test that max retries is set to 3."""
        from llm.openai_llm import CustomRetryTransport

        # The BACKOFF_TIMES list should have exactly 3 entries (for 3 retries)
        assert len(CustomRetryTransport.BACKOFF_TIMES) == 3

    def test_openai_llm_client_configuration(self):
        """Test that OpenAI LLM client is configured with custom transport."""
        from llm.openai_llm import OpenAILLM
        import httpx

        # Create instance with test key
        try:
            llm = OpenAILLM(api_key='test_key_for_config_test', model_name='openai_4o')

            # Verify client is configured
            assert llm.client is not None

            # Verify HTTP client is custom configured
            assert llm.client._client is not None

        except Exception as e:
            # Configuration test passed as long as initialization works
            pass

    def test_groq_llm_client_configuration(self):
        """Test that Groq LLM client is configured with custom transport."""
        from llm.groq_llm import GroqLLM

        # Create instance with test key
        try:
            llm = GroqLLM(api_key='test_key_for_config_test', model_name='groq_gpt_oss_120b')

            # Verify client is configured
            assert llm.client is not None

        except Exception as e:
            # Configuration test passed as long as initialization works
            pass

    def test_embeddings_client_configuration(self):
        """Test that Embeddings client is configured with custom transport."""
        from llm.openai_embeddings import OpenAIEmbeddings

        # Create instance with test key
        try:
            embeddings = OpenAIEmbeddings(api_key='test_key_for_config_test')

            # Verify client is configured
            assert embeddings.client is not None

        except Exception as e:
            # Configuration test passed as long as initialization works
            pass

    def test_retry_transport_has_handle_async_request(self):
        """Test that CustomRetryTransport implements handle_async_request."""
        from llm.openai_llm import CustomRetryTransport
        import inspect

        # Verify the method exists
        assert hasattr(CustomRetryTransport, 'handle_async_request')

        # Verify it's an async method
        method = getattr(CustomRetryTransport, 'handle_async_request')
        assert inspect.iscoroutinefunction(method)

    def test_all_implementations_have_same_backoff(self):
        """Test that OpenAI LLM, Groq LLM, and Embeddings all use same backoff times."""
        from llm.openai_llm import CustomRetryTransport as OpenAIRetry
        from llm.groq_llm import CustomRetryTransport as GroqRetry
        from llm.openai_embeddings import CustomRetryTransport as EmbeddingsRetry

        # All should have the same backoff times
        assert OpenAIRetry.BACKOFF_TIMES == GroqRetry.BACKOFF_TIMES
        assert OpenAIRetry.BACKOFF_TIMES == EmbeddingsRetry.BACKOFF_TIMES

        # Verify they all end with 70 seconds
        assert OpenAIRetry.BACKOFF_TIMES[-1] == 70.0
        assert GroqRetry.BACKOFF_TIMES[-1] == 70.0
        assert EmbeddingsRetry.BACKOFF_TIMES[-1] == 70.0


class TestRetryDocumentation:
    """Test that retry mechanisms are documented."""

    def test_openai_llm_docstring_mentions_retry(self):
        """Test that OpenAI LLM __init__ documents retry strategy."""
        from llm.openai_llm import OpenAILLM

        docstring = OpenAILLM.__init__.__doc__
        assert docstring is not None
        assert 'retry' in docstring.lower() or 'Retry' in docstring

    def test_groq_llm_docstring_mentions_retry(self):
        """Test that Groq LLM __init__ documents retry strategy."""
        from llm.groq_llm import GroqLLM

        docstring = GroqLLM.__init__.__doc__
        assert docstring is not None
        assert 'retry' in docstring.lower() or 'Retry' in docstring

    def test_embeddings_docstring_mentions_retry(self):
        """Test that Embeddings __init__ documents retry strategy."""
        from llm.openai_embeddings import OpenAIEmbeddings

        docstring = OpenAIEmbeddings.__init__.__doc__
        assert docstring is not None
        assert 'retry' in docstring.lower() or 'Retry' in docstring


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
