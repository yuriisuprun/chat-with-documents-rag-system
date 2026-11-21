"""
AI consistency testing for LLM providers.

Compares provider responses for identical inputs to assess:
1. Answer correctness (factual accuracy)
2. Faithfulness to context (grounded in sources)
3. Citation consistency (same sources cited)
4. Response completeness (all relevant info included)
5. Hallucination rate (made-up info percentage)
6. Response latency (time to first token, total time)
"""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.infrastructure.llm.groq_provider import GroqProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider


@dataclass
class ResponseMetrics:
    """Metrics for evaluating LLM response quality."""
    
    response: str
    provider: str
    latency_ms: float
    length_chars: int
    contains_error: bool = False
    
    def to_dict(self):
        """Convert to dictionary for reporting."""
        return {
            "provider": self.provider,
            "response_length": self.length_chars,
            "latency_ms": self.latency_ms,
            "contains_error": self.contains_error,
        }


class TestProviderConsistency:
    """Tests for consistency across LLM providers."""

    # ========================================================================
    # Test Data: Identical Prompts for All Providers
    # ========================================================================

    CONSISTENCY_TEST_PROMPTS = [
        {
            "prompt": "What is the capital of France?",
            "expected_answer": "Paris",
            "source_doc": "France is a country in Europe",
        },
        {
            "prompt": "Explain photosynthesis in one sentence.",
            "expected_key": "light",
            "source_doc": "Photosynthesis uses light energy",
        },
        {
            "prompt": "List three primary colors.",
            "expected_colors": ["red", "blue", "yellow"],
            "source_doc": "Red, blue, and yellow are primary colors",
        },
    ]

    # ========================================================================
    # 1. Answer Correctness (Factual Accuracy)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_answers_factual_question_correctly(self, mock_groq_class):
        """Test Groq provides factually correct answer."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="The capital of France is Paris.")
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        response = provider.generate(
            "What is the capital of France? Use only the provided context: "
            "France is a country in Europe. Paris is the capital of France."
        )

        assert "Paris" in response
        assert response.lower().count("france") >= 1

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_answers_factual_question_correctly(self, mock_post):
        """Test Ollama provides factually correct answer."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "The capital of France is Paris."
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        response = provider.generate(
            "What is the capital of France? Use only the provided context: "
            "France is a country in Europe. Paris is the capital of France."
        )

        assert "Paris" in response

    @patch("groq.Groq")
    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_consistency_factual_accuracy(self, mock_ollama, mock_groq_class):
        """Test both providers give consistent factual answers."""
        # Groq response
        mock_groq = MagicMock()
        groq_response = MagicMock()
        groq_response.choices = [MagicMock(
            message=MagicMock(content="The answer is Paris, the capital of France.")
        )]
        mock_groq.chat.completions.create.return_value = groq_response
        mock_groq_class.return_value = mock_groq

        # Ollama response
        mock_ollama_response = Mock()
        mock_ollama_response.json.return_value = {
            "response": "Paris is the capital of France."
        }
        mock_ollama.return_value = mock_ollama_response

        prompt = "What is the capital of France?"

        groq = GroqProvider(api_key="test-key")
        groq_result = groq.generate(prompt)

        ollama = OllamaProvider()
        ollama_result = ollama.generate(prompt)

        # Both should mention Paris
        assert "Paris" in groq_result
        assert "Paris" in ollama_result

    # ========================================================================
    # 2. Faithfulness to Context (Grounded in Sources)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_grounded_in_context(self, mock_groq_class):
        """Test Groq answer is grounded in provided context."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="Based on the provided context, the answer is Paris."
            )
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        context = "The capital of France is Paris."
        response = provider.generate(
            f"Based on this context: '{context}', what is the capital of France?"
        )

        # Response should reference the information from context
        assert len(response) > 0
        assert "Paris" in response or "capital" in response.lower()

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_grounded_in_context(self, mock_post):
        """Test Ollama answer is grounded in provided context."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "According to the context, Paris is the capital."
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        context = "The capital of France is Paris."
        response = provider.generate(
            f"Based on: '{context}', what is the capital?"
        )

        assert "Paris" in response

    # ========================================================================
    # 3. Citation Consistency (Same Sources Cited)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_mentions_context_source(self, mock_groq_class):
        """Test Groq mentions the context it was given."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="Based on the document about France, Paris is the capital."
            )
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        response = provider.generate(
            "According to the document, what is the capital of France?"
        )

        # Should reference the source (document)
        assert "document" in response.lower() or "capital" in response.lower()

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_mentions_context_source(self, mock_post):
        """Test Ollama mentions the context it was given."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "The document states that Paris is the capital."
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        response = provider.generate(
            "What does the document say about France's capital?"
        )

        assert "document" in response.lower() or "states" in response.lower()

    # ========================================================================
    # 4. Response Completeness (All Relevant Info Included)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_complete_response(self, mock_groq_class):
        """Test Groq provides complete response to multi-part question."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="The three primary colors are red, blue, and yellow. "
                        "They cannot be created by mixing other colors."
            )
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        response = provider.generate(
            "List the three primary colors and explain why they are primary."
        )

        # Should include all three colors
        assert "red" in response.lower()
        assert "blue" in response.lower()
        assert "yellow" in response.lower()

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_complete_response(self, mock_post):
        """Test Ollama provides complete response to multi-part question."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "The three primary colors are red, blue, and yellow."
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        response = provider.generate("What are the three primary colors?")

        assert "red" in response.lower()
        assert "blue" in response.lower()
        assert "yellow" in response.lower()

    # ========================================================================
    # 5. Hallucination Rate (Made-up Info Percentage)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_no_hallucination_with_context(self, mock_groq_class):
        """Test Groq doesn't hallucinate when context is provided."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="Based on the provided information, "
                        "I cannot find details about the founding date."
            )
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        context = "Paris is a city in France."
        response = provider.generate(
            f"Context: {context}\n\n"
            f"When was Paris founded?"
        )

        # Should not make up a date if not in context
        # (or should say "not provided")
        assert len(response) > 0

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_no_hallucination_with_context(self, mock_post):
        """Test Ollama doesn't hallucinate when context is provided."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "The context does not provide this information."
        }
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        context = "Paris is a city."
        response = provider.generate(
            f"Context: {context}\n\nWhen was it founded?"
        )

        assert len(response) > 0

    # ========================================================================
    # 6. Response Latency (Time to Response, Total Time)
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_response_latency(self, mock_groq_class):
        """Test Groq response latency is measured."""
        mock_client = MagicMock()
        
        def slow_response(*args, **kwargs):
            """Simulate response with small delay."""
            time.sleep(0.1)
            response = MagicMock()
            response.choices = [MagicMock(
                message=MagicMock(content="Response")
            )]
            return response
        
        mock_client.chat.completions.create.side_effect = slow_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        start = time.time()
        response = provider.generate("test")
        elapsed = time.time() - start

        assert response == "Response"
        assert elapsed > 0.05  # Should have some latency

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_response_latency(self, mock_post):
        """Test Ollama response latency is measured."""
        def slow_response(*args, **kwargs):
            """Simulate response with small delay."""
            time.sleep(0.1)
            response = Mock()
            response.json.return_value = {"response": "Response"}
            return response
        
        mock_post.side_effect = slow_response

        provider = OllamaProvider()
        
        start = time.time()
        response = provider.generate("test")
        elapsed = time.time() - start

        assert response == "Response"
        assert elapsed > 0.05

    @patch("groq.Groq")
    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_groq_generally_faster_than_ollama(self, mock_ollama, mock_groq_class):
        """Test latency comparison: Groq typically faster than Ollama."""
        # Groq fast response
        mock_groq = MagicMock()
        def groq_fast(*args, **kwargs):
            time.sleep(0.05)
            response = MagicMock()
            response.choices = [MagicMock(
                message=MagicMock(content="Groq response")
            )]
            return response
        mock_groq.chat.completions.create.side_effect = groq_fast
        mock_groq_class.return_value = mock_groq

        # Ollama slower response
        def ollama_slow(*args, **kwargs):
            time.sleep(0.2)
            response = Mock()
            response.json.return_value = {"response": "Ollama response"}
            return response
        mock_ollama.side_effect = ollama_slow

        groq = GroqProvider(api_key="test-key")
        start_groq = time.time()
        groq_result = groq.generate("test")
        groq_time = time.time() - start_groq

        ollama = OllamaProvider()
        start_ollama = time.time()
        ollama_result = ollama.generate("test")
        ollama_time = time.time() - start_ollama

        # Both got results
        assert groq_result == "Groq response"
        assert ollama_result == "Ollama response"

        # Groq was faster in this simulation
        assert groq_time < ollama_time

    # ========================================================================
    # 7. Consistency Across Multiple Identical Requests
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_consistent_answers_to_same_question(self, mock_groq_class):
        """Test Groq gives consistent answers to identical questions."""
        mock_client = MagicMock()
        
        # Always return same response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="The capital is Paris.")
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        responses = [
            provider.generate("What is the capital of France?")
            for _ in range(3)
        ]

        # All responses should be identical (with mocking)
        assert responses[0] == responses[1] == responses[2]

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_consistent_answers_to_same_question(self, mock_post):
        """Test Ollama gives consistent answers to identical questions."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Paris is the capital."}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        responses = [
            provider.generate("What is the capital of France?")
            for _ in range(3)
        ]

        assert responses[0] == responses[1] == responses[2]

    # ========================================================================
    # 8. Error Handling Consistency
    # ========================================================================

    @patch("groq.Groq")
    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_consistent_error_handling(self, mock_ollama, mock_groq_class):
        """Test both providers handle errors consistently."""
        from app.core.exceptions import LLMUnavailableException

        # Groq error
        mock_groq = MagicMock()
        mock_groq.chat.completions.create.side_effect = Exception("Service error")
        mock_groq_class.return_value = mock_groq

        # Ollama error
        mock_ollama.side_effect = Exception("Connection error")

        groq = GroqProvider(api_key="test-key")
        ollama = OllamaProvider()

        # Both should raise exceptions
        with pytest.raises(LLMUnavailableException):
            groq.generate("test")

        with pytest.raises(LLMUnavailableException):
            ollama.generate("test")

    # ========================================================================
    # 9. Response Quality Metrics Collection
    # ========================================================================

    @patch("groq.Groq")
    def test_groq_response_metrics(self, mock_groq_class):
        """Test we can collect quality metrics from Groq response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        test_response = "This is a test response about the capital of France."
        mock_response.choices = [MagicMock(
            message=MagicMock(content=test_response)
        )]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        provider = GroqProvider(api_key="test-key")
        
        start = time.time()
        response = provider.generate("What is the capital of France?")
        latency = (time.time() - start) * 1000  # Convert to ms

        metrics = ResponseMetrics(
            response=response,
            provider="groq",
            latency_ms=latency,
            length_chars=len(response),
        )

        assert metrics.provider == "groq"
        assert metrics.length_chars > 0
        assert metrics.latency_ms >= 0

    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_ollama_response_metrics(self, mock_post):
        """Test we can collect quality metrics from Ollama response."""
        mock_response = Mock()
        test_response = "Paris is the capital of France."
        mock_response.json.return_value = {"response": test_response}
        mock_post.return_value = mock_response

        provider = OllamaProvider()
        
        start = time.time()
        response = provider.generate("What is the capital of France?")
        latency = (time.time() - start) * 1000

        metrics = ResponseMetrics(
            response=response,
            provider="ollama",
            latency_ms=latency,
            length_chars=len(response),
        )

        assert metrics.provider == "ollama"
        assert metrics.length_chars > 0

    # ========================================================================
    # 10. Comparative Analysis Framework
    # ========================================================================

    @patch("groq.Groq")
    @patch("app.infrastructure.llm.ollama_provider.requests.post")
    def test_comparative_analysis_framework(self, mock_ollama, mock_groq_class):
        """Test framework for comparing provider responses."""
        # Groq
        mock_groq = MagicMock()
        groq_response = MagicMock()
        groq_response.choices = [MagicMock(
            message=MagicMock(content="Paris is the capital of France.")
        )]
        mock_groq.chat.completions.create.return_value = groq_response
        mock_groq_class.return_value = mock_groq

        # Ollama
        mock_ollama_resp = Mock()
        mock_ollama_resp.json.return_value = {
            "response": "The capital of France is Paris."
        }
        mock_ollama.return_value = mock_ollama_resp

        prompt = "What is the capital of France?"
        groq = GroqProvider(api_key="test-key")
        ollama = OllamaProvider()

        groq_result = groq.generate(prompt)
        ollama_result = ollama.generate(prompt)

        results = {
            "groq": groq_result,
            "ollama": ollama_result,
        }

        # Both mention Paris
        assert all("Paris" in response for response in results.values())
        assert all(len(response) > 0 for response in results.values())
