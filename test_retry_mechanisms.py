"""
Test suite for retry mechanisms in LLM and embedding implementations.

Tests verify that progressive retry backoff works correctly:
- Retry attempts: 5
- Backoff times: 2s, 5s, 15s, 30s, 70s (1 minute 10 seconds for last)
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx
from httpx import Response, Request
import time


class TestRetryMechanismBackoff:
    """Test progressive backoff timing."""

    @pytest.mark.asyncio
    async def test_openai_llm_retry_backoff_timing(self):
        """Test that OpenAI LLM retries with correct progressive backoff."""
        from llm.openai_llm import CustomRetryTransport

        transport = CustomRetryTransport()

        # Verify backoff times
        expected_backoffs = [2.0, 5.0, 15.0, 30.0, 70.0]
        assert transport.BACKOFF_TIMES == expected_backoffs
        assert len(transport.BACKOFF_TIMES) == 5

    @pytest.mark.asyncio
    async def test_groq_llm_retry_backoff_timing(self):
        """Test that Groq LLM retries with correct progressive backoff."""
        from llm.groq_llm import CustomRetryTransport

        transport = CustomRetryTransport()

        # Verify backoff times
        expected_backoffs = [2.0, 5.0, 15.0, 30.0, 70.0]
        assert transport.BACKOFF_TIMES == expected_backoffs
        assert len(transport.BACKOFF_TIMES) == 5

    @pytest.mark.asyncio
    async def test_embeddings_retry_backoff_timing(self):
        """Test that embeddings retry with correct progressive backoff."""
        from llm.openai_embeddings import CustomRetryTransport

        transport = CustomRetryTransport()

        # Verify backoff times
        expected_backoffs = [2.0, 5.0, 15.0, 30.0, 70.0]
        assert transport.BACKOFF_TIMES == expected_backoffs
        assert len(transport.BACKOFF_TIMES) == 5


class TestRetryOn429RateLimit:
    """Test retry behavior on rate limit errors (429)."""

    @pytest.mark.asyncio
    async def test_openai_transport_retries_on_429(self):
        """Test that OpenAI transport retries on 429 status code."""
        from llm.openai_llm import CustomRetryTransport

        # Create mock request
        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        # Create mock responses: 4x 429, then 1x 200
        mock_responses = [
            Response(429, json={"error": "rate_limit"}),
            Response(429, json={"error": "rate_limit"}),
            Response(200, json={"choices": [{"message": {"content": "success"}}]})
        ]

        call_count = 0
        start_times = []

        async def mock_handle(req):
            nonlocal call_count
            start_times.append(time.time())
            response = mock_responses[min(call_count, len(mock_responses) - 1)]
            call_count += 1
            return response

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            # Mock asyncio.sleep to avoid actual waiting
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                # Verify we got success
                assert response.status_code == 200

                # Verify we retried correct number of times
                assert call_count == 3  # Initial + 2 retries

                # Verify backoff times were correct
                assert sleep_times == [2.0, 5.0]


class TestRetryOn5xxServerErrors:
    """Test retry behavior on server errors (500+)."""

    @pytest.mark.asyncio
    async def test_transport_retries_on_500(self):
        """Test that transport retries on 500 server error."""
        from llm.openai_llm import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(500, json={"error": "server_error"})
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 3
                assert sleep_times == [2.0, 5.0]

    @pytest.mark.asyncio
    async def test_transport_retries_on_503(self):
        """Test that transport retries on 503 service unavailable."""
        from llm.groq_llm import CustomRetryTransport

        request = Request("POST", "https://api.groq.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Response(503, json={"error": "service_unavailable"})
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 2
                assert sleep_times == [2.0]


class TestRetryOnTimeouts:
    """Test retry behavior on timeout errors."""

    @pytest.mark.asyncio
    async def test_transport_retries_on_connect_timeout(self):
        """Test that transport retries on connection timeout."""
        from llm.openai_llm import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectTimeout("Connection timeout")
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 2
                assert sleep_times == [2.0]

    @pytest.mark.asyncio
    async def test_transport_retries_on_read_timeout(self):
        """Test that transport retries on read timeout."""
        from llm.groq_llm import CustomRetryTransport

        request = Request("POST", "https://api.groq.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ReadTimeout("Read timeout")
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 3
                assert sleep_times == [2.0, 5.0]


class TestMaxRetries:
    """Test that max retries is respected."""

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self):
        """Test that transport gives up after 5 retries."""
        from llm.openai_llm import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            # Always fail
            return Response(429, json={"error": "rate_limit"})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                # Should fail after max retries
                assert response.status_code == 429

                # Should have tried: initial + 5 retries = 6 total
                assert call_count == 6

                # Should have slept 5 times with progressive backoff
                assert sleep_times == [2.0, 5.0, 15.0, 30.0, 70.0]

                # Verify last backoff was 70 seconds (1 min 10 sec)
                assert sleep_times[-1] == 70.0

    @pytest.mark.asyncio
    async def test_timeout_max_retries(self):
        """Test that timeout errors respect max retries."""
        from llm.openai_embeddings import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/embeddings")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectTimeout("Connection timeout")

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                with pytest.raises(httpx.ConnectTimeout):
                    await transport.handle_async_request(request)

                # Should have tried: initial + 5 retries = 6 total
                assert call_count == 6

                # Should have slept 5 times
                assert sleep_times == [2.0, 5.0, 15.0, 30.0, 70.0]


class TestNoRetryOnSuccess:
    """Test that successful requests don't retry."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test that successful request on first attempt doesn't retry."""
        from llm.openai_llm import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 1  # Only one attempt
                assert sleep_times == []  # No sleeps


class TestProgressiveBackoffSequence:
    """Test the exact progressive backoff sequence."""

    @pytest.mark.asyncio
    async def test_full_progressive_backoff_sequence(self):
        """Test complete backoff sequence: 2s, 5s, 15s, 30s, 70s."""
        from llm.openai_llm import CustomRetryTransport

        request = Request("POST", "https://api.openai.com/v1/chat/completions")

        call_count = 0

        async def mock_handle(req):
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                return Response(429, json={"error": "rate_limit"})
            return Response(200, json={"success": True})

        transport = CustomRetryTransport()

        with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request', new=mock_handle):
            sleep_times = []

            async def mock_sleep(duration):
                sleep_times.append(duration)

            with patch('asyncio.sleep', new=mock_sleep):
                response = await transport.handle_async_request(request)

                assert response.status_code == 200
                assert call_count == 6  # Initial + 5 retries

                # Verify exact progressive backoff sequence
                assert len(sleep_times) == 5
                assert sleep_times[0] == 2.0   # 2 seconds
                assert sleep_times[1] == 5.0   # 5 seconds
                assert sleep_times[2] == 15.0  # 15 seconds
                assert sleep_times[3] == 30.0  # 30 seconds
                assert sleep_times[4] == 70.0  # 70 seconds (1 min 10 sec)

                # Total wait time across all retries
                total_wait = sum(sleep_times)
                assert total_wait == 122.0  # 2 + 5 + 15 + 30 + 70 = 122 seconds


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
