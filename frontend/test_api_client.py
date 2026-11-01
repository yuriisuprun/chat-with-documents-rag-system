"""
Unit tests for the API client.

Tests communication with the backend API without Streamlit.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from api_client import APIClient


@pytest.fixture
def api_client():
    """Create API client for testing."""
    return APIClient("http://localhost:8000")


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    return response


class TestAPIClientInitialization:
    """Test API client initialization."""

    def test_init_default_url(self):
        """Test initialization with default URL."""
        client = APIClient()
        assert client.base_url == "http://localhost:8000"

    def test_init_custom_url(self):
        """Test initialization with custom URL."""
        client = APIClient("http://example.com:9000")
        assert client.base_url == "http://example.com:9000"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slashes are stripped."""
        client = APIClient("http://example.com/")
        assert client.base_url == "http://example.com"


class TestDocumentOperations:
    """Test document-related API operations."""

    @patch("api_client.httpx.Client")
    def test_upload_document(self, mock_client, api_client):
        """Test uploading a document."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc_123",
            "filename": "test.pdf",
            "status": "indexed",
            "message": "Document uploaded",
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        file_obj = MagicMock()
        file_obj.name = "test.pdf"
        file_obj.getbuffer.return_value = b"PDF content"

        result = api_client.upload_document(file_obj)

        assert result["document_id"] == "doc_123"
        assert result["filename"] == "test.pdf"

    @patch("api_client.httpx.Client")
    def test_list_documents(self, mock_client, api_client):
        """Test listing documents."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "documents": [],
            "count": 0,
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.list_documents()

        assert result["count"] == 0
        assert isinstance(result["documents"], list)

    @patch("api_client.httpx.Client")
    def test_delete_document(self, mock_client, api_client):
        """Test deleting a document."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc_123",
            "message": "Document deleted (50 chunks removed)",
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.delete_document("doc_123")

        assert result["document_id"] == "doc_123"


class TestChatOperations:
    """Test chat/QA API operations."""

    @patch("api_client.httpx.Client")
    def test_ask_question_simple(self, mock_client, api_client):
        """Test asking a simple question."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "sources": [],
            "context_sufficient": True,
            "error": None,
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.ask_question("What is AI?")

        assert result["query"] == "What is AI?"
        assert len(result["answer"]) > 0
        assert result["context_sufficient"] is True

    @patch("api_client.httpx.Client")
    def test_ask_question_with_document_ids(self, mock_client, api_client):
        """Test asking question with specific document IDs."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": "What?",
            "answer": "Answer",
            "sources": [],
            "context_sufficient": True,
            "error": None,
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.ask_question(
            "What?",
            document_ids=["doc_1", "doc_2"],
        )

        assert result["query"] == "What?"

    @patch("api_client.httpx.Client")
    def test_ask_question_with_sources(self, mock_client, api_client):
        """Test question response with sources."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": "What is ML?",
            "answer": "ML is machine learning.",
            "sources": [
                {
                    "document_id": "doc_1",
                    "filename": "ai_book.pdf",
                    "page_number": 5,
                    "chunk_index": 0,
                    "similarity_score": 0.92,
                    "text_preview": "Machine learning...",
                }
            ],
            "context_sufficient": True,
            "error": None,
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.ask_question("What is ML?")

        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_id"] == "doc_1"


class TestHealthCheck:
    """Test health check operations."""

    @patch("api_client.httpx.Client")
    def test_check_health_healthy(self, mock_client, api_client):
        """Test health check when system is healthy."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "healthy",
            "services": {
                "ingestion": True,
                "retrieval": True,
                "rag": True,
            },
            "version": "0.1.0",
            "timestamp": "2024-01-01T12:00:00",
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.check_health()

        assert result["status"] == "healthy"
        assert all(result["services"].values())

    @patch("api_client.httpx.Client")
    def test_check_health_degraded(self, mock_client, api_client):
        """Test health check when system is degraded."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "degraded",
            "services": {
                "ingestion": True,
                "retrieval": False,
                "rag": True,
            },
            "version": "0.1.0",
            "timestamp": "2024-01-01T12:00:00",
        }
        mock_client.return_value.__enter__.return_value.request.return_value = (
            mock_response
        )

        result = api_client.check_health()

        assert result["status"] == "degraded"
        assert not result["services"]["retrieval"]


class TestErrorHandling:
    """Test error handling in API client."""

    @patch("api_client.httpx.Client")
    def test_timeout_error(self, mock_client, api_client):
        """Test timeout error handling."""
        import httpx

        mock_client.return_value.__enter__.return_value.request.side_effect = (
            httpx.TimeoutException("timeout")
        )

        with pytest.raises(Exception) as exc_info:
            api_client.ask_question("Test")

        assert "timed out" in str(exc_info.value).lower()

    @patch("api_client.httpx.Client")
    def test_http_error(self, mock_client, api_client):
        """Test HTTP error handling."""
        import httpx

        # Create mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"detail": "API Error"}
        mock_response.status_code = 500

        # Create mock request
        mock_request = MagicMock()

        # Create HTTPStatusError with proper attributes
        error = httpx.HTTPStatusError(
            "Internal Server Error",
            request=mock_request,
            response=mock_response,
        )
        # Set status_code on response for error handling
        error.response.status_code = 500

        mock_client.return_value.__enter__.return_value.request.side_effect = error

        with pytest.raises(Exception) as exc_info:
            api_client.ask_question("Test")

        # Check for error message (either from exception or status code)
        assert "error" in str(exc_info.value).lower() or "500" in str(exc_info.value)

    @patch("api_client.httpx.Client")
    def test_connection_error(self, mock_client, api_client):
        """Test connection error handling."""
        mock_client.return_value.__enter__.return_value.request.side_effect = (
            Exception("Connection refused")
        )

        with pytest.raises(Exception) as exc_info:
            api_client.ask_question("Test")

        assert "Connection error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
