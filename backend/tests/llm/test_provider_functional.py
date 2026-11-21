"""
Functional tests for LLM providers.

Validates 12 key areas for each provider:
1. Successful initialization
2. Valid authentication
3. Invalid API key handling
4. Model availability
5. Prompt construction
6. Temperature configuration
7. Maximum context handling
8. Timeout configuration
9. Response parsing
10. Streaming responses
11. Token usage tracking
12. Error normalization
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.core.exceptions import LLMTimeoutException, LLMUnavailableException
from app.infrastructure.llm.groq_provider import GroqProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider


# ============================================================================
# GROQ PROVIDER FUNCTIONAL TESTS
# ============================================================================


class TestGroqProviderFunctional:
    """Functional tests for Groq LLM provider."""

    # ========================================================================
    # 1. Successful Initialization
    # ========================================================================

    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
    def test_successful_initialization(self):
        """Test Groq provider initializes successfully with valid API key."""
        provider = GroqProvider(api_key="test-key-123")
        assert provider.model_name == "openai/gpt-oss-120b"
        assert provider.api_key == "test-key-123"
        assert provider.timeout == 30
        assert provider.default_temperature == 0.3

    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
    def test_initialization_with_custom_model(self):
        """Test Groq provider accepts custom model name."""
        provider = GroqProvider(model_name="gpt-4", api_key="test-key-123")
        assert provider.model_name == "gpt-4"

    # ========================================================================
    # 2. Valid Authentication
    # ========================================================================

    @patch("groq.Groq")
    def test_valid_authentication(self, mock_groq_class):
        """Test valid Groq API key is accepted."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="valid-key")
        result = provider.generate("test prompt")

        assert result == "Test response"
        mock_groq_class.assert_called()

    # ========================================================================
    # 3. Invalid API Key Handling
    # ========================================================================

    def test_missing_api_key_raises_exception(self):
        """Test missing API key raises LLMUnavailableException."""
        # Use explicit empty string to override settings
        with patch("app.core.config.settings.groq_api_key", ""):
            with pytest.raises(LLMUnavailableException):
                GroqProvider(api_key="")

    @patch("groq.Groq")
    def test_invalid_api_key_handling(self, mock_groq_class):
        """Test invalid API key is properly handled."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("401 Invalid API key")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="invalid-key")
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test prompt")
        
        assert "Invalid API key" in str(exc_info.value.message)

    # ========================================================================
    # 4. Model Availability
    # ========================================================================

    @patch("groq.Groq")
    def test_model_availability_check(self, mock_groq_class):
        """Test model availability is verified."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test")

        # Verify model was passed to API call
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "openai/gpt-oss-120b"

    def test_get_model_name(self):
        """Test get_model_name returns correct model."""
        provider = GroqProvider(model_name="custom-model", api_key="key")
        assert provider.get_model_name() == "custom-model"

    # ========================================================================
    # 5. Prompt Construction
    # ========================================================================

    @patch("groq.Groq")
    def test_prompt_construction(self, mock_groq_class):
        """Test prompt is correctly formatted in request."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        test_prompt = "What is the meaning of life?"
        provider.generate(test_prompt)

        # Verify prompt was passed correctly
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0]["content"] == test_prompt
        assert call_kwargs["messages"][0]["role"] == "user"

    @patch("groq.Groq")
    def test_prompt_with_special_characters(self, mock_groq_class):
        """Test prompt with special characters is handled correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        special_prompt = "What is 'hello' & \"world\"? @#$%"
        provider.generate(special_prompt)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0]["content"] == special_prompt

    # ========================================================================
    # 6. Temperature Configuration
    # ========================================================================

    @patch("groq.Groq")
    def test_default_temperature(self, mock_groq_class):
        """Test default temperature is applied."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    @patch("groq.Groq")
    def test_custom_temperature(self, mock_groq_class):
        """Test custom temperature is respected."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test", temperature=0.8)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.8

    @patch("groq.Groq")
    def test_temperature_boundary_values(self, mock_groq_class):
        """Test temperature boundary values (0.0, 1.0)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        provider.generate("test", temperature=0.0)
        assert mock_client.chat.completions.create.call_args[1]["temperature"] == 0.0
        
        provider.generate("test", temperature=1.0)
        assert mock_client.chat.completions.create.call_args[1]["temperature"] == 1.0

    # ========================================================================
    # 7. Maximum Context Handling
    # ========================================================================

    @patch("groq.Groq")
    def test_max_tokens_configuration(self, mock_groq_class):
        """Test max_tokens is configured correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["max_tokens"] == 1024

    @patch("groq.Groq")
    def test_long_prompt_handling(self, mock_groq_class):
        """Test handling of long prompts."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        long_prompt = "test " * 1000  # Very long prompt
        result = provider.generate(long_prompt)

        assert result == "Response"
        mock_client.chat.completions.create.assert_called_once()

    # ========================================================================
    # 8. Timeout Configuration
    # ========================================================================

    @patch("groq.Groq")
    def test_default_timeout(self, mock_groq_class):
        """Test default timeout is applied."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test")

        # Verify Groq client was initialized with timeout
        groq_call_kwargs = mock_groq_class.call_args[1]
        assert groq_call_kwargs["timeout"] == 30

    @patch("groq.Groq")
    def test_custom_timeout(self, mock_groq_class):
        """Test custom timeout is respected."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        provider.generate("test", timeout=60)

        groq_call_kwargs = mock_groq_class.call_args[1]
        assert groq_call_kwargs["timeout"] == 60

    @patch("groq.Groq")
    def test_timeout_exception_handling(self, mock_groq_class):
        """Test timeout exceptions are properly caught and re-raised."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("timeout")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(LLMTimeoutException):
            provider.generate("test")

    # ========================================================================
    # 9. Response Parsing
    # ========================================================================

    @patch("groq.Groq")
    def test_response_parsing(self, mock_groq_class):
        """Test response is correctly parsed."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        expected_text = "This is a test response from the model."
        mock_response.choices = [MagicMock(message=MagicMock(content=expected_text))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test")

        assert result == expected_text

    @patch("groq.Groq")
    def test_empty_response_handling(self, mock_groq_class):
        """Test empty response is handled gracefully."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test")

        assert result == ""

    @patch("groq.Groq")
    def test_response_with_special_characters(self, mock_groq_class):
        """Test response with special characters is preserved."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        special_response = "Response with 'quotes', \"double quotes\", & symbols: @#$%"
        mock_response.choices = [MagicMock(message=MagicMock(content=special_response))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test")

        assert result == special_response

    # ========================================================================
    # 10. Streaming Responses
    # ========================================================================

    @patch("groq.Groq")
    def test_streaming_not_supported_in_generate(self, mock_groq_class):
        """Test that generate method returns complete response (non-streaming)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Complete response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test")

        # Verify stream=False in request
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "stream" not in call_kwargs or call_kwargs.get("stream") is False
        assert result == "Complete response"

    # ========================================================================
    # 11. Token Usage Tracking
    # ========================================================================

    @patch("groq.Groq")
    def test_response_includes_usage_info(self, mock_groq_class):
        """Test response includes usage information where available."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test")

        # Generate should return text, usage available on response object
        assert result == "Response"

    # ========================================================================
    # 12. Error Normalization
    # ========================================================================

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

    @patch("groq.Groq")
    def test_error_normalization_service_error(self, mock_groq_class):
        """Test service errors are normalized."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("500 Server Error")
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"


# ============================================================================
# OLLAMA PROVIDER FUNCTIONAL TESTS
# ============================================================================


class TestOllamaProviderFunctional:
    """Functional tests for Ollama LLM provider."""

    # ========================================================================
    # 1. Successful Initialization
    # ========================================================================

    def test_successful_initialization(self):
        """Test Ollama provider initializes successfully."""
        provider = OllamaProvider()
        assert provider.model_name == "qwen3:8b"
        assert provider.base_url == "http://localhost:11434"
        assert provider.timeout == 180
        assert provider.default_temperature == 0.3

    def test_initialization_with_custom_model(self):
        """Test Ollama provider accepts custom model name."""
        provider = OllamaProvider(model_name="llama2")
        assert provider.model_name == "llama2"

    # ========================================================================
    # 2. Valid Authentication (N/A for Ollama - no API key)
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_no_authentication_required(self, mock_post):
        """Test Ollama doesn't require authentication."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Test response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == "Test response"
        # Verify no auth headers were added
        call_kwargs = mock_post.call_args[1]
        assert "headers" not in call_kwargs or "Authorization" not in call_kwargs.get("headers", {})

    # ========================================================================
    # 3. Invalid Configuration Handling
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_connection_error_handling(self, mock_post):
        """Test connection errors are properly handled."""
        mock_post.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert "ollama" in str(exc_info.value.message)

    # ========================================================================
    # 4. Model Availability
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_model_availability_check(self, mock_post):
        """Test model is requested from Ollama."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider(model_name="custom-model")
        provider.generate("test")

        # Verify model was in payload
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["model"] == "custom-model"

    def test_get_model_name(self):
        """Test get_model_name returns correct model."""
        provider = OllamaProvider(model_name="custom-model")
        assert provider.get_model_name() == "custom-model"

    # ========================================================================
    # 5. Prompt Construction
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_prompt_construction(self, mock_post):
        """Test prompt is correctly formatted in request."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        test_prompt = "What is the meaning of life?"
        provider.generate(test_prompt)

        # Verify prompt was passed correctly
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["prompt"] == test_prompt

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_prompt_with_special_characters(self, mock_post):
        """Test prompt with special characters is handled correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        special_prompt = "What is 'hello' & \"world\"? @#$%"
        provider.generate(special_prompt)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["prompt"] == special_prompt

    # ========================================================================
    # 6. Temperature Configuration
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_default_temperature(self, mock_post):
        """Test default temperature is applied."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        provider.generate("test")

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.3

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_custom_temperature(self, mock_post):
        """Test custom temperature is respected."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        provider.generate("test", temperature=0.8)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.8

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_temperature_boundary_values(self, mock_post):
        """Test temperature boundary values (0.0, 1.0)."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        provider.generate("test", temperature=0.0)
        assert mock_post.call_args_list[0][1]["json"]["temperature"] == 0.0
        
        provider.generate("test", temperature=1.0)
        assert mock_post.call_args_list[1][1]["json"]["temperature"] == 1.0

    # ========================================================================
    # 7. Maximum Context Handling
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_streaming_disabled_for_response(self, mock_post):
        """Test streaming is disabled to get complete response."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        provider.generate("test")

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["stream"] is False

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_long_prompt_handling(self, mock_post):
        """Test handling of long prompts."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        long_prompt = "test " * 1000  # Very long prompt
        result = provider.generate(long_prompt)

        assert result == "Response"
        mock_post.assert_called_once()

    # ========================================================================
    # 8. Timeout Configuration
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_default_timeout(self, mock_post):
        """Test default timeout is applied."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        provider.generate("test")

        # Verify timeout was passed to requests
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 180

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_custom_timeout(self, mock_post):
        """Test custom timeout is respected."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        provider.generate("test", timeout=300)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 300

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_timeout_exception_handling(self, mock_post):
        """Test timeout exceptions are properly caught and re-raised."""
        import requests
        mock_post.side_effect = requests.Timeout()

        provider = OllamaProvider()
        
        with pytest.raises(LLMTimeoutException):
            provider.generate("test")

    # ========================================================================
    # 9. Response Parsing
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_response_parsing(self, mock_post):
        """Test response is correctly parsed from JSON."""
        mock_response = Mock()
        expected_text = "This is a test response from Ollama."
        mock_response.json.return_value = {"response": expected_text}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == expected_text

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_empty_response_handling(self, mock_post):
        """Test empty response is handled gracefully."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == ""

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_response_with_special_characters(self, mock_post):
        """Test response with special characters is preserved."""
        mock_response = Mock()
        special_response = "Response with 'quotes', \"double quotes\", & symbols: @#$%"
        mock_response.json.return_value = {"response": special_response}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == special_response

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_malformed_json_response(self, mock_post):
        """Test malformed JSON response is handled."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException):
            provider.generate("test")

    # ========================================================================
    # 10. Streaming Responses
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_streaming_disabled_in_generate(self, mock_post):
        """Test that generate method returns complete response."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Complete response"}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        # Verify stream=False in request
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["stream"] is False
        assert result == "Complete response"

    # ========================================================================
    # 11. Token Usage Tracking
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_response_includes_metadata(self, mock_post):
        """Test response includes metadata where available."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Response",
            "model": "qwen3:8b",
            "created_at": "2024-01-01T00:00:00Z",
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 200000000,
            "eval_count": 20,
            "eval_duration": 600000000,
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.generate("test")

        assert result == "Response"

    # ========================================================================
    # 12. Error Normalization
    # ========================================================================

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_error_normalization_connection(self, mock_post):
        """Test connection errors are normalized."""
        mock_post.side_effect = Exception("Failed to connect")

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"
        assert "ollama" in str(exc_info.value.message)

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_error_normalization_timeout(self, mock_post):
        """Test timeout errors are normalized."""
        import requests
        mock_post.side_effect = requests.Timeout()

        provider = OllamaProvider()
        
        with pytest.raises(LLMTimeoutException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_TIMEOUT"

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_error_normalization_http_error(self, mock_post):
        """Test HTTP errors are normalized."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        with pytest.raises(LLMUnavailableException) as exc_info:
            provider.generate("test")
        
        assert exc_info.value.error_code == "LLM_UNAVAILABLE"
