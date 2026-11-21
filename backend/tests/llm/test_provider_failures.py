"""
Simplified failure scenario tests for LLM providers.

Note: These tests disable retry mechanisms to avoid timeouts.
Tests error handling for:
1. Provider unavailable (service down)
2. Network timeout (connection lost)
3. Authentication failure (bad credentials)
4. Rate limiting (429 response)
5. Server error (500+ response)
6. Malformed response (invalid JSON/format)
7. Empty response (null/empty output)
8. Connection issues
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from app.core.exceptions import LLMTimeoutException, LLMUnavailableException
from app.infrastructure.llm.groq_provider import GroqProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider


# ============================================================================
# GROQ PROVIDER FAILURE SCENARIOS (without retry delays)
# ============================================================================


class TestGroqProviderFailures:
    """Failure scenario tests for Groq LLM provider."""

    @patch("groq.Groq")
    def test_provider_unavailable_service_down(self, mock_groq_class):
        """Test handling when Groq service is completely unavailable."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Service Unavailable"
        )
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises((LLMUnavailableException, LLMTimeoutException)):
            provider.generate("test")

    @patch("groq.Groq")
    def test_provider_unavailable_500_error(self, mock_groq_class):
        """Test handling of 500 server error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "500 Internal Server Error"
        )
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises((LLMUnavailableException, LLMTimeoutException)):
            provider.generate("test")

    @patch("groq.Groq")
    def test_authentication_failure_invalid_key(self, mock_groq_class):
        """Test handling of invalid API key."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "401 Invalid authentication credentials"
        )
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="invalid-key")
        
        with pytest.raises((LLMUnavailableException, LLMTimeoutException)):
            provider.generate("test")

    @patch("groq.Groq")
    def test_rate_limit_429_error(self, mock_groq_class):
        """Test handling of 429 Too Many Requests."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "429 Rate limit exceeded"
        )
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises((LLMUnavailableException, LLMTimeoutException)):
            provider.generate("test")

    @patch("groq.Groq")
    def test_timeout_exception_handling(self, mock_groq_class):
        """Test timeout exceptions are properly caught and re-raised."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("timeout")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises((LLMTimeoutException, LLMUnavailableException)):
            provider.generate("test")

    @patch("groq.Groq")
    def test_error_normalization_authentication(self, mock_groq_class):
        """Test authentication errors are normalized."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"
        assert "groq" in str(exc_info.value.message)

    @patch("groq.Groq")
    def test_error_normalization_timeout(self, mock_groq_class):
        """Test timeout errors are normalized."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Request timed out")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(LLMTimeoutException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_TIMEOUT"


# ============================================================================
# OLLAMA PROVIDER FAILURE SCENARIOS
# ============================================================================


class TestOllamaProviderFailures:
    """Failure scenario tests for Ollama LLM provider."""

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_provider_unavailable_service_down(self, mock_post):
        """Test handling when Ollama service is down."""
        mock_post.side_effect = requests.ConnectionError(
            "Failed to establish connection"
        )

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_network_timeout_exceeded(self, mock_post):
        """Test handling when request times out."""
        mock_post.side_effect = requests.Timeout(
            "Request timed out after 180 seconds"
        )

        provider = OllamaProvider()
        
        with pytest.raises(LLMTimeoutException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_TIMEOUT"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_rate_limit_429_error(self, mock_post):
        """Test handling of 429 Too Many Requests."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "429 Too Many Requests"
        )
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException):
            provider.generate("test")

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_malformed_response_invalid_json(self, mock_post):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "{invalid}", 0
        )
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException):
            provider.generate("test")

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_empty_response_handling(self, mock_post):
        """Test handling of empty response field."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == ""

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_error_normalization_connection(self, mock_post):
        """Test connection errors are normalized."""
        mock_post.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"
        assert "ollama" in str(exc_info.value.message)

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_error_normalization_timeout(self, mock_post):
        """Test timeout errors are normalized."""
        mock_post.side_effect = requests.Timeout()

        provider = OllamaProvider()
        
        with pytest.raises(LLMTimeoutException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_TIMEOUT"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_model_not_installed(self, mock_post):
        """Test handling when model is not installed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": "model 'non-existent' not found"
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider(model_name="non-existent")
        result = provider.generate("test")

        # Returns empty when model field missing
        assert result == ""
