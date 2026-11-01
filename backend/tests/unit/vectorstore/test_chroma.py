"""
Unit tests for ChromaDB vector store.

Tests adding, searching, and deleting chunks.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import IndexingException, RetrievalException
from app.infrastructure.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def temp_dir():
    """Create temporary directory for test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vector_store(temp_dir):
    """Create ChromaDB vector store with temp directory."""
    with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
        mock_settings.chromadb_persist_dir = str(temp_dir)
        mock_settings.chroma_directory = temp_dir
        mock_settings.chromadb_collection_name = "test_collection"

        store = ChromaVectorStore()
        yield store


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return [
        [0.1, 0.2, 0.3, 0.4],  # Embedding 1
        [0.2, 0.3, 0.4, 0.5],  # Embedding 2
        [0.3, 0.4, 0.5, 0.6],  # Embedding 3
    ]


class TestChromaVectorStore:
    """Test ChromaDB vector store operations."""

    def test_vector_store_initialization(self, vector_store):
        """Test that vector store initializes."""
        assert vector_store is not None
        assert vector_store.collection is not None

    def test_add_chunks(self, vector_store, sample_embeddings):
        """Test adding chunks to vector store."""
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        texts = [
            "This is the first chunk",
            "This is the second chunk",
            "This is the third chunk",
        ]
        metadata_list = [
            {"document_id": "doc_1", "page_number": 1},
            {"document_id": "doc_1", "page_number": 2},
            {"document_id": "doc_2", "page_number": 1},
        ]

        # Add chunks
        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=sample_embeddings,
            metadata_list=metadata_list,
        )

        # Verify
        size = vector_store.get_collection_size()
        assert size == 3

    def test_search_returns_results(self, vector_store, sample_embeddings):
        """Test searching for similar chunks."""
        # Add chunks
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        texts = ["First text", "Second text", "Third text"]
        metadata_list = [
            {"document_id": "doc_1"},
            {"document_id": "doc_1"},
            {"document_id": "doc_2"},
        ]

        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=sample_embeddings,
            metadata_list=metadata_list,
        )

        # Search with query embedding (similar to first embedding)
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        results = vector_store.search(query_embedding, top_k=2)

        assert len(results) <= 2
        assert all(hasattr(r, "chunk_id") for r in results)
        assert all(hasattr(r, "similarity_score") for r in results)
        assert all(0 <= r.similarity_score <= 1 for r in results)

    def test_search_with_filter(self, vector_store, sample_embeddings):
        """Test searching with document filter."""
        # Add chunks
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        texts = ["First", "Second", "Third"]
        metadata_list = [
            {"document_id": "doc_1"},
            {"document_id": "doc_1"},
            {"document_id": "doc_2"},
        ]

        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=sample_embeddings,
            metadata_list=metadata_list,
        )

        # Search filtered to doc_1
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        filter_dict = {"document_id": {"$in": ["doc_1"]}}
        results = vector_store.search(query_embedding, top_k=10, filter_dict=filter_dict)

        # Should only get results from doc_1
        assert all(r.metadata["document_id"] == "doc_1" for r in results)

    def test_delete_chunks(self, vector_store, sample_embeddings):
        """Test deleting chunks."""
        # Add chunks
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        texts = ["First", "Second", "Third"]
        metadata_list = [{"document_id": "doc_1"}] * 3

        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=sample_embeddings,
            metadata_list=metadata_list,
        )

        assert vector_store.get_collection_size() == 3

        # Delete first chunk
        vector_store.delete_chunks(["chunk_1"])

        assert vector_store.get_collection_size() == 2

    def test_delete_document(self, vector_store, sample_embeddings):
        """Test deleting all chunks for a document."""
        # Add chunks
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        texts = ["First", "Second", "Third"]
        metadata_list = [
            {"document_id": "doc_1"},
            {"document_id": "doc_1"},
            {"document_id": "doc_2"},
        ]

        vector_store.add_chunks(
            chunk_ids=chunk_ids,
            texts=texts,
            embeddings=sample_embeddings,
            metadata_list=metadata_list,
        )

        # Delete doc_1
        vector_store.delete_document("doc_1")

        # Should have only 1 chunk left (from doc_2)
        assert vector_store.get_collection_size() == 1

    def test_get_collection_size(self, vector_store, sample_embeddings):
        """Test getting collection size."""
        assert vector_store.get_collection_size() == 0

        # Add chunks
        vector_store.add_chunks(
            chunk_ids=["chunk_1", "chunk_2"],
            texts=["First", "Second"],
            embeddings=sample_embeddings[:2],
            metadata_list=[{"document_id": "doc_1"}] * 2,
        )

        assert vector_store.get_collection_size() == 2

    def test_clear_collection(self, vector_store, sample_embeddings):
        """Test clearing collection."""
        # Add chunks
        vector_store.add_chunks(
            chunk_ids=["chunk_1", "chunk_2", "chunk_3"],
            texts=["First", "Second", "Third"],
            embeddings=sample_embeddings,
            metadata_list=[{"document_id": "doc_1"}] * 3,
        )

        assert vector_store.get_collection_size() == 3

        # Clear
        vector_store.clear()

        assert vector_store.get_collection_size() == 0

    def test_search_with_no_results(self, vector_store):
        """Test searching when no results match filter."""
        # Add chunks
        sample_embeddings = [[0.1, 0.2, 0.3, 0.4]]
        vector_store.add_chunks(
            chunk_ids=["chunk_1"],
            texts=["First"],
            embeddings=sample_embeddings,
            metadata_list=[{"document_id": "doc_1"}],
        )

        # Search with filter that matches nothing
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        filter_dict = {"document_id": {"$in": ["nonexistent"]}}
        results = vector_store.search(query_embedding, filter_dict=filter_dict)

        assert len(results) == 0


class TestChromaVectorStoreErrors:
    """Test error handling in ChromaDB vector store."""

    def test_add_chunks_error_handling(self, vector_store):
        """Test error handling when adding chunks fails."""
        # Simulate error by passing invalid data
        with pytest.raises(IndexingException):
            vector_store.add_chunks(
                chunk_ids=["chunk_1"],
                texts=["text"],
                embeddings=[[0.1, 0.2]],  # Wrong dimension
                metadata_list=[{"document_id": "doc_1"}],
            )

    def test_delete_nonexistent_document(self, vector_store):
        """Test deleting non-existent document doesn't raise error."""
        # Should not raise error
        vector_store.delete_document("nonexistent_doc")
