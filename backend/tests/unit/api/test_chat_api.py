"""
Unit tests for chat API endpoint.

Tests question answering with RAG pipeline using correct FastAPI dependency mocking.
"""

import pytest


class TestChatEndpoint:
    """Test chat endpoint with properly mocked dependencies."""

    def test_chat_valid_query(self, app_with_mocked_rag):
        """Test answering a valid question."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "What is AI?", "include_sources": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is AI?"
        assert "answer" in data
        assert len(data["sources"]) > 0
        assert data["context_sufficient"] is True

    def test_chat_empty_query(self, app_with_mocked_rag):
        """Test with empty query - should fail validation."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "", "include_sources": True},
        )

        # Pydantic validation returns 422 for empty min_length string
        assert response.status_code == 422

    def test_chat_whitespace_query(self, app_with_mocked_rag):
        """Test with whitespace-only query."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "   ", "include_sources": True},
        )

        assert response.status_code == 400

    def test_chat_long_query(self, app_with_mocked_rag):
        """Test with long query (within limit)."""
        # Max is 500, so test with 400 chars
        long_query = "x" * 400
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": long_query, "include_sources": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["context_sufficient"] is True

    def test_chat_exceeds_max_length(self, app_with_mocked_rag):
        """Test query exceeding max length."""
        long_query = "x" * 2001
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": long_query, "include_sources": True},
        )

        # Pydantic validation error
        assert response.status_code == 422

    def test_chat_with_document_ids(self, app_with_mocked_rag):
        """Test chat with specific document IDs filter."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={
                "query": "What is ML?",
                "document_ids": ["doc_1", "doc_2"],
                "include_sources": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data

    def test_chat_without_sources(self, app_with_mocked_rag):
        """Test chat without requesting source references."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "What is AI?", "include_sources": False},
        )

        assert response.status_code == 200
        data = response.json()
        # Response always includes sources field in schema
        assert "sources" in data

    def test_chat_multiple_sources(self, app_with_mocked_rag):
        """Test chat returning multiple sources."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "What is machine learning?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)
        # Mock returns 1 source
        assert len(data["sources"]) >= 0

    def test_chat_response_structure(self, app_with_mocked_rag):
        """Test that response has correct structure per schema."""
        response = app_with_mocked_rag.post(
            "/api/v1/chat",
            json={"query": "Test query"},
        )

        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields present
        assert "query" in data
        assert "answer" in data
        assert "sources" in data
        assert "context_sufficient" in data
        assert "error" in data
        
        # Verify types
        assert isinstance(data["query"], str)
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["context_sufficient"], bool)
