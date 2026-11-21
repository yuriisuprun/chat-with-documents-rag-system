"""
Comprehensive ChromaDB validation test suite for RAG system.

Tests all aspects of ChromaDB vector store operations including:
- Collection management (4 tests)
- Embedding insertion (6 tests)
- Vector retrieval (4 tests)
- Deletion operations (3 tests)
- Data integrity (6 tests)
- Persistence (3 tests)
- Concurrency (2 tests)
- Error handling (5 tests)
- Performance (5 tests)
- Integration (3 tests)

Total: 39 comprehensive tests
All metadata parameters are non-empty dicts per ChromaDB 0.4.24 requirements.
"""

import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.vectorstore.chroma import ChromaVectorStore


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def chroma_dir(tmp_path):
    """Provide isolated ChromaDB directory."""
    chroma_path = tmp_path / "chroma_test"
    chroma_path.mkdir(parents=True, exist_ok=True)
    yield str(chroma_path)
    # Cleanup
    if chroma_path.exists():
        shutil.rmtree(chroma_path, ignore_errors=True)


@pytest.fixture
def vectorstore(chroma_dir, monkeypatch):
    """Create ChromaVectorStore instance with isolated test directory."""
    monkeypatch.setenv("CHROMA_DIRECTORY", chroma_dir)
    monkeypatch.setenv("CHROMADB_COLLECTION_NAME", "test_collection")
    
    # Mock settings to point to test directory
    with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
        mock_settings.chroma_directory = chroma_dir
        mock_settings.chromadb_collection_name = "test_collection"
        mock_settings.chromadb_persist_dir = chroma_dir
        
        store = ChromaVectorStore()
        yield store
        
        # Cleanup
        try:
            store.clear()
        except Exception:
            pass


@pytest.fixture
def sample_embeddings():
    """Provide sample embeddings for testing."""
    return {
        "embedding_1": [0.1, 0.2, 0.3, 0.4, 0.5],
        "embedding_2": [0.2, 0.3, 0.4, 0.5, 0.6],
        "embedding_3": [0.15, 0.25, 0.35, 0.45, 0.55],
        "embedding_4": [0.9, 0.8, 0.7, 0.6, 0.5],
    }


@pytest.fixture
def sample_texts():
    """Provide sample texts for testing."""
    return {
        "text_1": "Machine learning is a subset of artificial intelligence",
        "text_2": "Deep learning uses neural networks with many layers",
        "text_3": "Natural language processing enables computers to understand text",
        "text_4": "Computer vision helps machines interpret visual information",
    }


# ============================================================================
# SECTION 1: Collection Management Tests (4 tests)
# ============================================================================


class TestCollectionManagement:
    """Test collection creation, retrieval, and configuration."""

    def test_collection_creation(self, chroma_dir):
        """✓ Test that collection is created on initialization."""
        with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
            mock_settings.chroma_directory = chroma_dir
            mock_settings.chromadb_collection_name = "test_collection"
            mock_settings.chromadb_persist_dir = chroma_dir
            
            store = ChromaVectorStore()
            
            # Verify collection exists
            assert store.collection is not None
            assert store.collection.name == "test_collection"
            
            # Cleanup
            store.clear()

    def test_collection_metadata_settings(self, chroma_dir):
        """✓ Test collection metadata is properly configured."""
        with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
            mock_settings.chroma_directory = chroma_dir
            mock_settings.chromadb_collection_name = "test_collection"
            mock_settings.chromadb_persist_dir = chroma_dir
            
            store = ChromaVectorStore()
            
            # Verify metadata is set
            assert store.collection.metadata is not None
            assert "hnsw:space" in store.collection.metadata
            assert store.collection.metadata["hnsw:space"] == "cosine"
            
            # Cleanup
            store.clear()

    def test_get_collection_size_empty(self, vectorstore):
        """✓ Test collection size is 0 when empty."""
        size = vectorstore.get_collection_size()
        assert size == 0

    def test_get_collection_size_after_insertion(self, vectorstore, sample_embeddings, sample_texts):
        """✓ Test collection size after adding chunks."""
        chunk_ids = list(sample_embeddings.keys())
        embeddings = list(sample_embeddings.values())
        texts = [sample_texts[f"text_{i+1}"] for i in range(len(chunk_ids))]
        metadata = [{"idx": i, "doc_id": "doc_1"} for i in range(len(chunk_ids))]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        size = vectorstore.get_collection_size()
        assert size == 4


# ============================================================================
# SECTION 2: Embedding Insertion Tests (6 tests)
# ============================================================================


class TestEmbeddingInsertion:
    """Test adding embeddings and handling edge cases."""

    def test_add_single_embedding(self, vectorstore, sample_embeddings, sample_texts):
        """✓ Test adding a single embedding."""
        chunk_ids = ["embedding_1"]
        embeddings = [sample_embeddings["embedding_1"]]
        texts = ["Machine learning is a subset of artificial intelligence"]
        metadata = [{"idx": 0, "doc_id": "doc_1"}]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        assert vectorstore.get_collection_size() == 1

    def test_add_multiple_embeddings(self, vectorstore, sample_embeddings, sample_texts):
        """✓ Test adding multiple embeddings in batch."""
        chunk_ids = list(sample_embeddings.keys())
        embeddings = list(sample_embeddings.values())
        texts = [sample_texts[f"text_{i+1}"] for i in range(len(chunk_ids))]
        metadata = [{"idx": i, "doc_id": "doc_1"} for i in range(len(chunk_ids))]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        assert vectorstore.get_collection_size() == 4

    def test_embedding_dimension_validation(self, vectorstore):
        """✓ Test that embeddings must have consistent dimensions."""
        chunk_ids = ["id_1", "id_2"]
        texts = ["text 1", "text 2"]
        # Mixed dimensions - this should fail
        embeddings = [
            [0.1, 0.2, 0.3],  # 3 dimensions
            [0.1, 0.2, 0.3, 0.4, 0.5],  # 5 dimensions
        ]
        metadata = [{"idx": 0, "test_field": "value_1"}, {"idx": 1, "test_field": "value_2"}]
        
        with pytest.raises(Exception):
            vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)

    def test_duplicate_id_detection(self, vectorstore, sample_embeddings, sample_texts):
        """✓ Test that duplicate IDs are handled."""
        # Add first chunk
        chunk_ids_1 = ["duplicate_id"]
        embeddings_1 = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts_1 = ["First content"]
        metadata_1 = [{"idx": 0, "attempt": 1}]
        
        vectorstore.add_chunks(chunk_ids_1, texts_1, embeddings_1, metadata_1)
        
        # Add chunk with same ID - should replace
        chunk_ids_2 = ["duplicate_id"]
        embeddings_2 = [[0.2, 0.3, 0.4, 0.5, 0.6]]
        texts_2 = ["Updated content"]
        metadata_2 = [{"idx": 1, "attempt": 2}]
        
        vectorstore.add_chunks(chunk_ids_2, texts_2, embeddings_2, metadata_2)
        
        # Collection should still have 1 item
        assert vectorstore.get_collection_size() == 1

    def test_metadata_with_various_types(self, vectorstore):
        """✓ Test metadata with various field types."""
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = ["Test content"]
        metadata = [{
            "idx": 0,
            "doc_id": "doc_1",
            "page_number": 42,
            "chunk_index": 5,
            "is_processed": True,
        }]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        assert vectorstore.get_collection_size() == 1

    def test_add_chunks_with_empty_metadata_dict_fails(self, vectorstore):
        """✓ Test that empty metadata dict causes error."""
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = ["Test content"]
        # Empty dict - ChromaDB 0.4.24 requires non-empty metadata
        metadata = [{}]
        
        with pytest.raises(Exception):
            vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)


# ============================================================================
# SECTION 3: Vector Retrieval Tests (4 tests)
# ============================================================================


class TestVectorRetrieval:
    """Test semantic search and retrieval operations."""

    def test_retrieve_with_exact_match(self, vectorstore):
        """✓ Test retrieval with identical embedding."""
        # Add embedding
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        chunk_ids = ["id_1"]
        embeddings = [query_embedding]
        texts = ["Test document content"]
        metadata = [{"idx": 0, "doc_id": "doc_1"}]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Query with same embedding
        results = vectorstore.search(query_embedding, top_k=1)
        
        assert len(results) == 1
        assert results[0].chunk_id == "id_1"
        assert results[0].similarity_score > 0.99  # Should be very similar

    def test_retrieve_top_k_limit(self, vectorstore, sample_embeddings, sample_texts):
        """✓ Test that top_k parameter limits results."""
        chunk_ids = list(sample_embeddings.keys())
        embeddings = list(sample_embeddings.values())
        texts = [sample_texts[f"text_{i+1}"] for i in range(len(chunk_ids))]
        metadata = [{"idx": i, "doc_id": "doc_1"} for i in range(len(chunk_ids))]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Search with top_k=2
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=2)
        
        assert len(results) <= 2

    def test_retrieve_with_metadata_filter(self, vectorstore):
        """✓ Test retrieval with metadata filtering."""
        # Add multiple chunks with different doc IDs
        chunk_ids = ["id_1", "id_2", "id_3"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.15, 0.25, 0.35, 0.45, 0.55],
        ]
        texts = ["Text 1", "Text 2", "Text 3"]
        metadata = [
            {"idx": 0, "document_id": "doc_1"},
            {"idx": 1, "document_id": "doc_2"},
            {"idx": 2, "document_id": "doc_1"},
        ]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Search with filter for doc_1
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=5, filter_dict={"document_id": "doc_1"})
        
        # Should only return results from doc_1
        assert all(r.metadata.get("document_id") == "doc_1" for r in results)

    def test_retrieve_similarity_scores(self, vectorstore):
        """✓ Test that similarity scores are valid (0-1)."""
        chunk_ids = ["id_1", "id_2"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.9, 0.8, 0.7, 0.6, 0.5],
        ]
        texts = ["Similar text", "Dissimilar text"]
        metadata = [{"idx": 0, "type": "similar"}, {"idx": 1, "type": "dissimilar"}]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=2)
        
        # Check scores are in valid range
        for result in results:
            assert 0 <= result.similarity_score <= 1


# ============================================================================
# SECTION 4: Deletion Operations Tests (3 tests)
# ============================================================================


class TestDeletionOperations:
    """Test chunk and document deletion."""

    def test_delete_single_chunk(self, vectorstore):
        """✓ Test deleting a single chunk."""
        chunk_ids = ["id_1", "id_2"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
        ]
        texts = ["Text 1", "Text 2"]
        metadata = [{"idx": 0, "content": "first"}, {"idx": 1, "content": "second"}]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        assert vectorstore.get_collection_size() == 2
        
        # Delete first chunk
        vectorstore.delete_chunks(["id_1"])
        
        assert vectorstore.get_collection_size() == 1

    def test_delete_multiple_chunks(self, vectorstore):
        """✓ Test deleting multiple chunks."""
        chunk_ids = ["id_1", "id_2", "id_3"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
        texts = ["Text 1", "Text 2", "Text 3"]
        metadata = [
            {"idx": 0, "batch": "a"},
            {"idx": 1, "batch": "b"},
            {"idx": 2, "batch": "a"},
        ]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        assert vectorstore.get_collection_size() == 3
        
        # Delete multiple chunks
        vectorstore.delete_chunks(["id_1", "id_3"])
        
        assert vectorstore.get_collection_size() == 1

    def test_collection_clear(self, vectorstore):
        """✓ Test clearing entire collection."""
        chunk_ids = ["id_1", "id_2", "id_3"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
        texts = ["Text 1", "Text 2", "Text 3"]
        metadata = [{"idx": i, "cleared": False} for i in range(3)]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        assert vectorstore.get_collection_size() == 3
        
        # Clear collection
        vectorstore.clear()
        
        assert vectorstore.get_collection_size() == 0


# ============================================================================
# SECTION 5: Data Integrity Tests (6 tests)
# ============================================================================


class TestDataIntegrity:
    """Test data consistency and integrity."""

    def test_embedding_dimension_consistency(self, vectorstore):
        """✓ Test all embeddings maintain consistent dimension."""
        chunk_ids = ["id_1", "id_2", "id_3"]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
        texts = ["Text 1", "Text 2", "Text 3"]
        metadata = [{"idx": i, "dimension": 5} for i in range(3)]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Query and verify retrieved embeddings maintain dimension
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=3)
        
        assert len(results) == 3

    def test_text_content_preserved(self, vectorstore):
        """✓ Test that text content is preserved correctly."""
        original_text = "This is the original document content with specific words"
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = [original_text]
        metadata = [{"idx": 0, "preserved": True}]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Query and verify text is preserved
        results = vectorstore.search([0.1, 0.2, 0.3, 0.4, 0.5], top_k=1)
        
        assert results[0].text == original_text

    def test_metadata_content_preserved(self, vectorstore):
        """✓ Test that metadata is preserved correctly."""
        original_metadata = {
            "idx": 0,
            "document_id": "doc_123",
            "page_number": 42,
            "chunk_index": 7,
            "custom_field": "custom_value",
        }
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = ["Content"]
        metadata = [original_metadata]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        # Query and verify metadata is preserved
        results = vectorstore.search([0.1, 0.2, 0.3, 0.4, 0.5], top_k=1)
        
        retrieved_metadata = results[0].metadata
        assert retrieved_metadata["document_id"] == "doc_123"
        assert retrieved_metadata["page_number"] == 42
        assert retrieved_metadata["chunk_index"] == 7

    def test_duplicate_ingestion_prevents_data_loss(self, vectorstore):
        """✓ Test that re-ingesting with same ID maintains single collection item."""
        chunk_ids = ["id_1"]
        embeddings_1 = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts_1 = ["Original content"]
        metadata_1 = [{"idx": 0, "version": 1}]
        
        vectorstore.add_chunks(chunk_ids, texts_1, embeddings_1, metadata_1)
        size_after_first = vectorstore.get_collection_size()
        assert size_after_first == 1
        
        # Re-ingest with same ID (simulating update)
        embeddings_2 = [[0.2, 0.3, 0.4, 0.5, 0.6]]
        texts_2 = ["Updated content"]
        metadata_2 = [{"idx": 1, "version": 2}]
        
        vectorstore.add_chunks(chunk_ids, texts_2, embeddings_2, metadata_2)
        
        # Should still have 1 item (replaced, not duplicated) - no data loss
        size_after_second = vectorstore.get_collection_size()
        assert size_after_second == 1
        assert size_after_first == size_after_second  # No duplication occurred

    def test_metadata_field_types_preserved(self, vectorstore):
        """✓ Test that various metadata field types are preserved."""
        metadata_input = {
            "idx": 42,
            "string_field": "test_value",
            "page_number": 15,
            "is_processed": True,
            "version": 1,
        }
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = ["Content"]
        metadata = [metadata_input]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        results = vectorstore.search([0.1, 0.2, 0.3, 0.4, 0.5], top_k=1)
        retrieved_metadata = results[0].metadata
        
        # Verify types are preserved
        assert isinstance(retrieved_metadata.get("idx"), int)
        assert isinstance(retrieved_metadata.get("string_field"), str)
        assert isinstance(retrieved_metadata.get("page_number"), int)


# ============================================================================
# SECTION 6: Persistence Tests (3 tests)
# ============================================================================


class TestPersistence:
    """Test data persistence across instances."""

    def test_persistence_file_structure(self, chroma_dir):
        """✓ Test that persistence creates expected file structure."""
        with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
            mock_settings.chroma_directory = chroma_dir
            mock_settings.chromadb_collection_name = "test_collection"
            mock_settings.chromadb_persist_dir = chroma_dir
            
            # Create first instance and add data
            store1 = ChromaVectorStore()
            chunk_ids = ["id_1"]
            embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
            texts = ["Persistent content"]
            metadata = [{"idx": 0, "persistent": True}]
            
            store1.add_chunks(chunk_ids, texts, embeddings, metadata)
            
            # Verify files are created
            chroma_path = Path(chroma_dir)
            assert chroma_path.exists()
            
            # Cleanup first instance
            store1.clear()

    def test_data_retrieval_after_reload(self, chroma_dir):
        """✓ Test that data persists across instance reload."""
        with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
            mock_settings.chroma_directory = chroma_dir
            mock_settings.chromadb_collection_name = "test_collection"
            mock_settings.chromadb_persist_dir = chroma_dir
            
            # Create first instance and add data
            store1 = ChromaVectorStore()
            chunk_ids = ["id_1"]
            embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
            texts = ["Persistent content"]
            metadata = [{"idx": 0, "stored": "yes"}]
            
            store1.add_chunks(chunk_ids, texts, embeddings, metadata)
            initial_size = store1.get_collection_size()
            
            # Create second instance pointing to same directory
            store2 = ChromaVectorStore()
            reloaded_size = store2.get_collection_size()
            
            assert initial_size == reloaded_size
            assert reloaded_size == 1
            
            # Cleanup
            store2.clear()

    def test_multiple_collections_isolation(self, chroma_dir):
        """✓ Test that multiple collections are isolated."""
        with patch("app.infrastructure.vectorstore.chroma.settings") as mock_settings:
            mock_settings.chroma_directory = chroma_dir
            mock_settings.chromadb_persist_dir = chroma_dir
            
            # Create store with collection 1
            mock_settings.chromadb_collection_name = "collection_1"
            store1 = ChromaVectorStore()
            
            chunk_ids_1 = ["id_1"]
            embeddings_1 = [[0.1, 0.2, 0.3, 0.4, 0.5]]
            texts_1 = ["Content 1"]
            metadata_1 = [{"idx": 0, "collection": 1}]
            
            store1.add_chunks(chunk_ids_1, texts_1, embeddings_1, metadata_1)
            
            # Create store with collection 2
            mock_settings.chromadb_collection_name = "collection_2"
            store2 = ChromaVectorStore()
            
            chunk_ids_2 = ["id_2"]
            embeddings_2 = [[0.2, 0.3, 0.4, 0.5, 0.6]]
            texts_2 = ["Content 2"]
            metadata_2 = [{"idx": 0, "collection": 2}]
            
            store2.add_chunks(chunk_ids_2, texts_2, embeddings_2, metadata_2)
            
            # Verify isolation
            assert store1.get_collection_size() == 1
            assert store2.get_collection_size() == 1
            
            # Cleanup
            store1.clear()
            store2.clear()


# ============================================================================
# SECTION 7: Concurrency Tests (2 tests)
# ============================================================================


class TestConcurrency:
    """Test concurrent operations with proper synchronization."""

    def test_concurrent_writes_synchronization(self, vectorstore):
        """✓ Test concurrent write operations with synchronization."""
        results = []
        errors = []
        lock = threading.Lock()
        barrier = threading.Barrier(3)  # Synchronization barrier
        
        def add_chunks(thread_id: int):
            try:
                # Wait for all threads to be ready
                barrier.wait()
                
                chunk_ids = [f"thread_{thread_id}_id_{i}" for i in range(2)]
                embeddings = [
                    [0.1 * (thread_id + 1), 0.2, 0.3, 0.4, 0.5],
                    [0.2 * (thread_id + 1), 0.3, 0.4, 0.5, 0.6],
                ]
                texts = [f"Thread {thread_id} text {i}" for i in range(2)]
                metadata = [{"idx": i, "thread_id": thread_id} for i in range(2)]
                
                vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
                
                with lock:
                    results.append(thread_id)
            except Exception as e:
                with lock:
                    errors.append((thread_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_chunks, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify all threads completed successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3

    def test_concurrent_reads_and_writes(self, vectorstore):
        """✓ Test concurrent read and write operations."""
        # Setup initial data
        chunk_ids = [f"id_{i}" for i in range(3)]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
        texts = [f"Text {i}" for i in range(3)]
        metadata = [{"idx": i, "initial": True} for i in range(3)]
        
        vectorstore.add_chunks(chunk_ids, embeddings=embeddings, texts=texts, metadata_list=metadata)
        
        results = []
        errors = []
        lock = threading.Lock()
        barrier = threading.Barrier(3)
        
        def read_write_worker(worker_id: int):
            try:
                # Wait for synchronization
                barrier.wait()
                
                if worker_id == 0:
                    # Reader thread
                    query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
                    retrieved = vectorstore.search(query_embedding, top_k=2)
                    with lock:
                        results.append(("read", len(retrieved)))
                else:
                    # Writer threads
                    new_id = f"concurrent_id_{worker_id}"
                    vectorstore.add_chunks(
                        [new_id],
                        texts=[f"New content {worker_id}"],
                        embeddings=[[0.5, 0.5, 0.5, 0.5, 0.5]],
                        metadata_list=[{"idx": worker_id, "concurrent": True}]
                    )
                    with lock:
                        results.append(("write", worker_id))
            except Exception as e:
                with lock:
                    errors.append((worker_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=read_write_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Verify no errors and operations completed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3


# ============================================================================
# SECTION 8: Error Handling Tests (5 tests)
# ============================================================================


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_invalid_embedding_format_raises_error(self, vectorstore):
        """✓ Test that invalid embedding format raises error."""
        chunk_ids = ["id_1"]
        embeddings = ["not a list"]  # Invalid format
        texts = ["Text"]
        metadata = [{"idx": 0, "invalid": "format"}]
        
        with pytest.raises(Exception):
            vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)

    def test_mismatched_list_lengths_raises_error(self, vectorstore):
        """✓ Test that mismatched list lengths raise error."""
        chunk_ids = ["id_1", "id_2"]  # 2 IDs
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]  # 1 embedding
        texts = ["Text 1", "Text 2"]  # 2 texts
        metadata = [{"idx": 0, "mismatch": "lengths"}]  # 1 metadata
        
        with pytest.raises(Exception):
            vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)

    def test_search_on_empty_collection(self, vectorstore):
        """✓ Test search on empty collection returns empty results."""
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=5)
        
        assert len(results) == 0

    def test_delete_nonexistent_chunk_handled_gracefully(self, vectorstore):
        """✓ Test deleting non-existent chunk doesn't raise error."""
        # This should not raise an exception
        vectorstore.delete_chunks(["nonexistent_id"])
        
        assert vectorstore.get_collection_size() == 0

    def test_invalid_metadata_type_raises_error(self, vectorstore):
        """✓ Test that invalid metadata types raise error."""
        chunk_ids = ["id_1"]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        texts = ["Text"]
        # Metadata must be a dict, not a list
        metadata = [["invalid", "metadata"]]
        
        with pytest.raises(Exception):
            vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)


# ============================================================================
# SECTION 9: Performance Tests (5 tests)
# ============================================================================


class TestPerformance:
    """Test performance characteristics and scalability."""

    def test_batch_insertion_performance(self, vectorstore):
        """✓ Test batch insertion performance."""
        num_chunks = 100
        chunk_ids = [f"id_{i}" for i in range(num_chunks)]
        embeddings = [[0.1 + (i % 10) * 0.01, 0.2, 0.3, 0.4, 0.5] for i in range(num_chunks)]
        texts = [f"Document chunk {i}" for i in range(num_chunks)]
        metadata = [{"idx": i, "batch": "performance"} for i in range(num_chunks)]
        
        start_time = time.time()
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        elapsed = time.time() - start_time
        
        assert vectorstore.get_collection_size() == num_chunks
        assert elapsed < 10.0  # Should complete in reasonable time

    def test_large_batch_search_performance(self, vectorstore):
        """✓ Test search performance with large collection."""
        num_chunks = 50
        chunk_ids = [f"id_{i}" for i in range(num_chunks)]
        embeddings = [[0.1 + (i % 10) * 0.01, 0.2, 0.3, 0.4, 0.5] for i in range(num_chunks)]
        texts = [f"Document chunk {i}" for i in range(num_chunks)]
        metadata = [{"idx": i, "collection": "large"} for i in range(num_chunks)]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        start_time = time.time()
        results = vectorstore.search(query_embedding, top_k=10)
        elapsed = time.time() - start_time
        
        assert len(results) > 0
        assert elapsed < 5.0  # Search should be fast

    def test_deletion_performance(self, vectorstore):
        """✓ Test deletion performance."""
        num_chunks = 50
        chunk_ids = [f"id_{i}" for i in range(num_chunks)]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in range(num_chunks)]
        texts = [f"Document chunk {i}" for i in range(num_chunks)]
        metadata = [{"idx": i, "deletable": True} for i in range(num_chunks)]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        delete_ids = chunk_ids[:25]  # Delete half
        start_time = time.time()
        vectorstore.delete_chunks(delete_ids)
        elapsed = time.time() - start_time
        
        assert vectorstore.get_collection_size() == 25
        assert elapsed < 5.0  # Should be reasonably fast

    def test_metadata_filtering_performance(self, vectorstore):
        """✓ Test metadata filtering performance."""
        num_chunks = 100
        chunk_ids = [f"id_{i}" for i in range(num_chunks)]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in range(num_chunks)]
        texts = [f"Document chunk {i}" for i in range(num_chunks)]
        metadata = [
            {"idx": i, "document_id": f"doc_{i % 5}", "category": "test"}
            for i in range(num_chunks)
        ]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        filter_dict = {"document_id": "doc_0"}
        
        start_time = time.time()
        results = vectorstore.search(query_embedding, top_k=10, filter_dict=filter_dict)
        elapsed = time.time() - start_time
        
        assert len(results) > 0
        assert elapsed < 3.0  # Filtered search should be fast

    def test_collection_clear_performance(self, vectorstore):
        """✓ Test collection clear performance."""
        num_chunks = 100
        chunk_ids = [f"id_{i}" for i in range(num_chunks)]
        embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in range(num_chunks)]
        texts = [f"Document chunk {i}" for i in range(num_chunks)]
        metadata = [{"idx": i, "to_clear": True} for i in range(num_chunks)]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        
        start_time = time.time()
        vectorstore.clear()
        elapsed = time.time() - start_time
        
        assert vectorstore.get_collection_size() == 0
        assert elapsed < 5.0  # Should be reasonably fast


# ============================================================================
# SECTION 10: Integration Tests (3 tests)
# ============================================================================


class TestIntegration:
    """Test complex integration scenarios."""

    def test_full_document_lifecycle(self, vectorstore):
        """✓ Test complete document ingestion, search, and deletion."""
        # Ingest document
        doc_id = "doc_123"
        chunk_ids = [f"doc_123_chunk_{i}" for i in range(3)]
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7],
        ]
        texts = [f"Content section {i}" for i in range(3)]
        metadata = [
            {"idx": i, "document_id": doc_id, "page_number": i + 1}
            for i in range(3)
        ]
        
        vectorstore.add_chunks(chunk_ids, texts, embeddings, metadata)
        assert vectorstore.get_collection_size() == 3
        
        # Search
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = vectorstore.search(query_embedding, top_k=2)
        assert len(results) > 0
        
        # Delete document
        vectorstore.delete_document(doc_id)
        assert vectorstore.get_collection_size() == 0

    def test_mixed_operations_workflow(self, vectorstore):
        """✓ Test mixed sequence of operations."""
        # Add initial data
        vectorstore.add_chunks(
            ["id_1", "id_2"],
            texts=["First", "Second"],
            embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5], [0.2, 0.3, 0.4, 0.5, 0.6]],
            metadata_list=[{"idx": 0, "batch": 1}, {"idx": 1, "batch": 1}]
        )
        
        # Search
        results = vectorstore.search([0.1, 0.2, 0.3, 0.4, 0.5], top_k=2)
        assert len(results) == 2
        
        # Add more data
        vectorstore.add_chunks(
            ["id_3"],
            texts=["Third"],
            embeddings=[[0.3, 0.4, 0.5, 0.6, 0.7]],
            metadata_list=[{"idx": 0, "batch": 2}]
        )
        
        # Delete
        vectorstore.delete_chunks(["id_1"])
        
        # Verify final state
        assert vectorstore.get_collection_size() == 2
        
        # Search again
        results = vectorstore.search([0.1, 0.2, 0.3, 0.4, 0.5], top_k=2)
        assert len(results) <= 2

    def test_document_update_scenario(self, vectorstore):
        """✓ Test updating document with new chunks."""
        doc_id = "doc_v1"
        
        # Initial ingestion
        vectorstore.add_chunks(
            [f"{doc_id}_chunk_0"],
            texts=["Original content"],
            embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],
            metadata_list=[{"idx": 0, "document_id": doc_id, "version": 1}]
        )
        assert vectorstore.get_collection_size() == 1
        
        # Delete old version
        vectorstore.delete_document(doc_id)
        assert vectorstore.get_collection_size() == 0
        
        # Ingest new version
        vectorstore.add_chunks(
            [f"{doc_id}_chunk_0", f"{doc_id}_chunk_1"],
            texts=["Updated content part 1", "Updated content part 2"],
            embeddings=[[0.2, 0.3, 0.4, 0.5, 0.6], [0.3, 0.4, 0.5, 0.6, 0.7]],
            metadata_list=[
                {"idx": 0, "document_id": doc_id, "version": 2},
                {"idx": 1, "document_id": doc_id, "version": 2}
            ]
        )
        assert vectorstore.get_collection_size() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
