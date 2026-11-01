"""
Unit tests for chat API endpoint.

Tests question answering with RAG pipeline.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.chat import router
from app.core.exceptions import RAGException
from app.core.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_rag_service():
    """Create mock RAG service."""
    service = MagicMock()
    service.answer_question.return_value = {
        "query": "What is machine learning?",
        "answer": "Machine learning is a field of artificial intelligence that enables systems to learn from data.",
        "sources": [
            {
                "document_id": "doc_1",
                "filename": "ai_book.pdf",
                "page_number": 5,
                "chunk_index": 0,
                "similarity_score": 0.92,
                "text_preview": "Machine learning is a field of AI...",
            }
        ],
        "context_sufficient": True,
        "retrieval_count": 4,
    }
    return service


class TestChatEndpoint:
    """Test chat endpoint."""

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_valid_query(self, mock_get_rag, client):
        """Test answering a valid question."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "sources": [
                {
                    "document_id": "doc_1",
                    "filename": "test.pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "similarity_score": 0.95,
                    "text_preview": "AI is...",
                }
            ],
            "context_sufficient": True,
            "retrieval_count": 4,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is AI?", "include_sources": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is AI?"
        assert "answer" in data
        assert len(data["sources"]) > 0
        assert data["context_sufficient"] is True

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_empty_query(self, mock_get_rag, client):
        """Test with empty query."""
        response = client.post(
            "/api/v1/chat",
            json={"query": "", "include_sources": True},
        )

        # Pydantic validation returns 422 for empty min_length string
        assert response.status_code == 422

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_whitespace_query(self, mock_get_rag, client):
        """Test with whitespace-only query."""
        response = client.post(
            "/api/v1/chat",
            json={"query": "   ", "include_sources": True},
        )

        assert response.status_code == 400

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_long_query(self, mock_get_rag, client):
        """Test with very long query."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "x" * 2000,
            "answer": "Answer",
            "sources": [],
            "context_sufficient": False,
            "retrieval_count": 0,
        }

        long_query = "x" * 2000
        response = client.post(
            "/api/v1/chat",
            json={"query": long_query, "include_sources": True},
        )

        assert response.status_code == 200

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_exceeds_max_length(self, mock_get_rag, client):
        """Test query exceeding max length."""
        long_query = "x" * 2001
        response = client.post(
            "/api/v1/chat",
            json={"query": long_query, "include_sources": True},
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_with_document_ids(self, mock_get_rag, client):
        """Test chat with specific document IDs."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "What is ML?",
            "answer": "ML is machine learning.",
            "sources": [],
            "context_sufficient": True,
            "retrieval_count": 2,
        }

        response = client.post(
            "/api/v1/chat",
            json={
                "query": "What is ML?",
                "document_ids": ["doc_1", "doc_2"],
                "include_sources": True,
            },
        )

        assert response.status_code == 200
        # Verify document_ids was passed to RAG service
        mock_rag.answer_question.assert_called_once()
        call_args = mock_rag.answer_question.call_args
        assert call_args[1]["document_ids"] == ["doc_1", "doc_2"]

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_without_sources(self, mock_get_rag, client):
        """Test chat without source references."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "sources": [
                {
                    "document_id": "doc_1",
                    "filename": "test.pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "similarity_score": 0.95,
                    "text_preview": "AI is...",
                }
            ],
            "context_sufficient": True,
            "retrieval_count": 4,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is AI?", "include_sources": False},
        )

        assert response.status_code == 200
        data = response.json()
        # Response always includes sources field
        assert "sources" in data

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_insufficient_context(self, mock_get_rag, client):
        """Test when context is insufficient."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "Very specific technical question?",
            "answer": "I don't have enough context to answer this.",
            "sources": [],
            "context_sufficient": False,
            "retrieval_count": 0,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "Very specific technical question?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["context_sufficient"] is False

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_rag_exception(self, mock_get_rag, client):
        """Test handling of RAG exception."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.side_effect = RAGException("RAG pipeline failed")

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is AI?"},
        )

        assert response.status_code == 500

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_unexpected_error(self, mock_get_rag, client):
        """Test handling of unexpected error."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.side_effect = Exception("Unexpected error")

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is AI?"},
        )

        assert response.status_code == 500

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_multiple_sources(self, mock_get_rag, client):
        """Test chat returning multiple sources."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "What is machine learning?",
            "answer": "ML is a field of AI.",
            "sources": [
                {
                    "document_id": "doc_1",
                    "filename": "ai_book.pdf",
                    "page_number": 5,
                    "chunk_index": 0,
                    "similarity_score": 0.92,
                    "text_preview": "Machine learning...",
                },
                {
                    "document_id": "doc_1",
                    "filename": "ai_book.pdf",
                    "page_number": 8,
                    "chunk_index": 1,
                    "similarity_score": 0.85,
                    "text_preview": "Neural networks...",
                },
            ],
            "context_sufficient": True,
            "retrieval_count": 4,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is machine learning?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2
        assert all("document_id" in s for s in data["sources"])
        assert all("filename" in s for s in data["sources"])
        assert all("page_number" in s for s in data["sources"])

    @patch("app.api.routes.chat.get_rag_service")
    def test_chat_response_structure(self, mock_get_rag, client):
        """Test that response has correct structure."""
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.answer_question.return_value = {
            "query": "Test query",
            "answer": "Test answer",
            "sources": [],
            "context_sufficient": True,
            "retrieval_count": 0,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "Test query"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "sources" in data
        assert "context_sufficient" in data
        assert "error" in data
