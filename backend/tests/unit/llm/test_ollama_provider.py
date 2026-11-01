"""
Unit tests for Ollama LLM provider.

Tests text generation, error handling, and timeouts.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import LLMTimeoutException, LLMUnavailableException
from app.infrastructure.llm.ollama_provider import OllamaProvider


@pytest.fixture
def ollama_provider():
    """Create Ollama provider instance."""
    return OllamaProvider(model_name="test-model")


class TestOllamaProvider:
    """Test Ollama LLM provider."""

    def test_provider_initialization(self, ollama_provider):
        """Test that provider initializes correctly."""
        assert ollama_provider is not None
        assert ollama_provider.model_name == "test-model"
        assert ollama_provider.base_url is not None

    def test_get_model_name(self, ollama_provider):
        """Test getting model name."""
        name = ollama_provider.get_model_name()

        assert name == "test-model"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_success(self, mock_post, ollama_provider):
        """Test successful text generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Generated text response"}
        mock_post.return_value = mock_response

        result = ollama_provider.generate("Test prompt")

        assert result == "Generated text response"
        mock_post.assert_called_once()

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_with_temperature(self, mock_post, ollama_provider):
        """Test generation with custom temperature."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        ollama_provider.generate("Prompt", temperature=0.7)

        # Check that temperature was passed
        call_args = mock_post.call_args
        assert call_args[1]["json"]["temperature"] == 0.7

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_timeout(self, mock_post, ollama_provider):
        """Test timeout handling."""
        import requests

        mock_post.side_effect = requests.Timeout()

        with pytest.raises(LLMTimeoutException):
            ollama_provider.generate("Prompt")

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_connection_error(self, mock_post, ollama_provider):
        """Test connection error handling."""
        import requests

        mock_post.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(LLMUnavailableException):
            ollama_provider.generate("Prompt")

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_empty_response(self, mock_post, ollama_provider):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        result = ollama_provider.generate("Prompt")

        assert result == ""

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_with_timeout_param(self, mock_post, ollama_provider):
        """Test custom timeout parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        ollama_provider.generate("Prompt", timeout=30)

        # Check that timeout was passed
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_http_error(self, mock_post, ollama_provider):
        """Test HTTP error handling."""
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_post.return_value = mock_response

        with pytest.raises(LLMUnavailableException):
            ollama_provider.generate("Prompt")

    def test_ollama_provider_custom_model(self):
        """Test creating provider with custom model."""
        provider = OllamaProvider(model_name="custom-model:13b")

        assert provider.get_model_name() == "custom-model:13b"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_generate_long_response(self, mock_post, ollama_provider):
        """Test handling of long generated text."""
        long_text = "A" * 5000  # 5000 character response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": long_text}
        mock_post.return_value = mock_response

        result = ollama_provider.generate("Prompt")

        assert len(result) == 5000
        assert result == long_text
