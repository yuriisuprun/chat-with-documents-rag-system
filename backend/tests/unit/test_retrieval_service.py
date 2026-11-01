"""
Unit tests for retrieval service.

Tests semantic search and indexing operations.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.pdf.models import Chunk
from app.services.retrieval_service import RetrievalService


@pytest.fixture
def mock_embedding_provider():
    """Create mock embedding provider."""
    provider = MagicMock()
    provider.embed_text.return_value = [0.1, 0.2, 0.3, 0.4]
    provider.embed_texts.return_value = [
        [0.1, 0.2, 0.3, 0.4],
        [0.2, 0.3, 0.4, 0.5],
    ]
    provider.get_embedding_dimension.return_value = 4
    provider.get_model_name.return_value = "test-model"
    return provider


@pytest.fixture
def mock_vector_store():
    """Create mock vector store."""
    store = MagicMock()
    store.search.return_value = [
        MagicMock(
            chunk_id="chunk_1",
            text="First result",
            similarity_score=0.95,
            metadata={"document_id": "doc_1", "page_number": 1},
        ),
        MagicMock(
            chunk_id="chunk_2",
            text="Second result",
            similarity_score=0.85,
            metadata={"document_id": "doc_1", "page_number": 2},
        ),
    ]
    store.get_collection_size.return_value = 10
    return store


@pytest.fixture
def retrieval_service(mock_embedding_provider, mock_vector_store):
    """Create retrieval service with mocks."""
    return RetrievalService(
        embedding_provider=mock_embedding_provider,
        vector_store=mock_vector_store,
    )


class TestRetrievalService:
    """Test retrieval service operations."""

    def test_retrieve_returns_chunks(self, retrieval_service, mock_vector_store):
        """Test that retrieve returns retrieved chunks."""
        query = "What is machine learning?"

        results = retrieval_service.retrieve(query, top_k=2)

        assert len(results) == 2
        assert results[0].chunk_id == "chunk_1"
        assert results[0].similarity_score == 0.95

    def test_retrieve_calls_embedding_provider(
        self, retrieval_service, mock_embedding_provider
    ):
        """Test that retrieve calls embedding provider."""
        query = "Test query"

        retrieval_service.retrieve(query)

        # Should have been called with query
        mock_embedding_provider.embed_text.assert_called_with(query)

    def test_retrieve_passes_embedding_to_vector_store(
        self, retrieval_service, mock_vector_store, mock_embedding_provider
    ):
        """Test that retrieve passes embedding to vector store."""
        query = "Test query"

        retrieval_service.retrieve(query)

        # Should have called search with embedding
        mock_vector_store.search.assert_called()
        call_args = mock_vector_store.search.call_args
        assert call_args[1]["query_embedding"] == [0.1, 0.2, 0.3, 0.4]

    def test_retrieve_with_document_filter(
        self, retrieval_service, mock_vector_store
    ):
        """Test that document filter is applied."""
        query = "Test query"
        doc_ids = ["doc_1", "doc_2"]

        retrieval_service.retrieve(query, document_ids=doc_ids)

        # Check that filter was passed
        call_args = mock_vector_store.search.call_args
        assert call_args[1]["filter_dict"] is not None

    def test_index_document_calls_embedding_provider(
        self, retrieval_service, mock_embedding_provider, mock_vector_store
    ):
        """Test that indexing calls embedding provider."""
        chunks = [
            Chunk(
                chunk_id="chunk_1",
                document_id="doc_1",
                filename="test.pdf",
                page_number=1,
                chunk_index=0,
                text="First chunk",
                text_length=11,
            ),
            Chunk(
                chunk_id="chunk_2",
                document_id="doc_1",
                filename="test.pdf",
                page_number=1,
                chunk_index=1,
                text="Second chunk",
                text_length=12,
            ),
        ]

        retrieval_service.index_document(chunks, "test-model")

        # Should have embedded texts
        mock_embedding_provider.embed_texts.assert_called()
        call_args = mock_embedding_provider.embed_texts.call_args
        assert len(call_args[0][0]) == 2

    def test_index_document_returns_chunk_count(
        self, retrieval_service, mock_embedding_provider
    ):
        """Test that index_document returns correct chunk count."""
        chunks = [
            Chunk(
                chunk_id="chunk_1",
                document_id="doc_1",
                filename="test.pdf",
                page_number=1,
                chunk_index=0,
                text="First chunk",
                text_length=11,
            ),
        ]

        count = retrieval_service.index_document(chunks, "test-model")

        assert count == 1

    def test_index_document_with_empty_chunks(self, retrieval_service):
        """Test indexing with empty chunk list."""
        count = retrieval_service.index_document([], "test-model")

        assert count == 0

    def test_delete_document_chunks(
        self, retrieval_service, mock_vector_store
    ):
        """Test deleting document chunks."""
        # Set up mock to track deletion
        mock_vector_store.get_collection_size.side_effect = [10, 8]  # Before and after

        deleted = retrieval_service.delete_document_chunks("doc_1")

        assert deleted == 2
        mock_vector_store.delete_document.assert_called_with("doc_1")

    def test_get_collection_stats(
        self, retrieval_service, mock_embedding_provider, mock_vector_store
    ):
        """Test getting collection statistics."""
        stats = retrieval_service.get_collection_stats()

        assert "chunk_count" in stats
        assert "embedding_dimension" in stats
        assert "embedding_model" in stats
        assert stats["chunk_count"] == 10
        assert stats["embedding_dimension"] == 4
        assert stats["embedding_model"] == "test-model"

    def test_retrieve_top_k_parameter(self, retrieval_service, mock_vector_store):
        """Test that top_k parameter is passed through."""
        query = "Test query"

        retrieval_service.retrieve(query, top_k=5)

        call_args = mock_vector_store.search.call_args
        assert call_args[1]["top_k"] == 5


class TestRetrievalServiceIntegration:
    """Integration tests for retrieval service."""

    def test_retrieve_full_workflow(self, retrieval_service):
        """Test complete retrieval workflow."""
        query = "What is artificial intelligence?"

        results = retrieval_service.retrieve(query, top_k=2)

        # Should return results
        assert len(results) > 0
        assert hasattr(results[0], "chunk_id")
        assert hasattr(results[0], "text")
        assert hasattr(results[0], "similarity_score")

    def test_index_and_retrieve_workflow(
        self, retrieval_service, mock_embedding_provider, mock_vector_store
    ):
        """Test indexing followed by retrieval."""
        # Index document
        chunks = [
            Chunk(
                chunk_id="chunk_1",
                document_id="doc_1",
                filename="test.pdf",
                page_number=1,
                chunk_index=0,
                text="Machine learning is AI",
                text_length=22,
            ),
        ]

        count = retrieval_service.index_document(chunks, "test-model")
        assert count == 1

        # Then retrieve
        results = retrieval_service.retrieve("What is AI?")
        assert len(results) > 0
