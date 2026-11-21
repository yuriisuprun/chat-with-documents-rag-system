"""
Pytest configuration and shared fixtures.

Provides common setup and fixtures for tests with proper resource cleanup.
"""

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set testing environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["TEST_MODE"] = "true"


# ============================================================================
# Database fixtures with proper cleanup (Phase 1: Resource leak fixes)
# ============================================================================

@contextmanager
def session_context():
    """Context manager for database operations with proper cleanup."""
    from app.db.database import SessionLocal
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # CRITICAL: Always close the session
        session.close()


@pytest.fixture
def db_session():
    """
    Provide database session with proper cleanup.
    
    This fixture ensures that database connections are always closed,
    preventing ResourceWarning: unclosed database errors.
    """
    from app.db.database import SessionLocal
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        # CRITICAL: Always close the session to prevent resource leaks
        session.close()


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service for testing."""
    service = MagicMock()
    service.answer_question.return_value = {
        "query": "Test question?",
        "answer": "Test answer.",
        "sources": [
            {
                "document_id": "doc_1",
                "filename": "test.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "similarity_score": 0.95,
                "text_preview": "Test context...",
            }
        ],
        "context_sufficient": True,
        "retrieval_count": 4,
    }
    return service


@pytest.fixture
def mock_ingestion_service():
    """Create a mock ingestion service for testing."""
    service = MagicMock()
    service.ingest_pdf.return_value = {
        "document_id": "test_doc_id",
        "filename": "test.pdf",
        "page_count": 5,
        "chunk_count": 20,
        "total_indexed": 20,
        "chunks": [
            {
                "chunk_id": f"chunk_{i}",
                "text": f"Test chunk {i}",
                "metadata": {
                    "document_id": "test_doc_id",
                    "page_number": 1,
                    "chunk_index": i,
                }
            }
            for i in range(20)
        ],
        "document_metadata": MagicMock(
            sha256="abc123",
            embedding_model="test-model"
        ),
    }
    return service


@pytest.fixture
def mock_retrieval_service():
    """Create a mock retrieval service for testing."""
    service = MagicMock()
    service.index_document.return_value = 20
    service.delete_document_chunks.return_value = 20
    service.get_collection_stats.return_value = {
        "chunk_count": 100,
        "embedding_model": "test-model",
    }
    service.vector_store = MagicMock()
    service.vector_store.collection = MagicMock()
    service.vector_store.collection.get.return_value = {
        "metadatas": [
            {"document_id": "doc_1", "filename": "test.pdf"}
        ]
    }
    return service


@pytest.fixture
def app_with_mocked_rag(mock_rag_service):
    """Provide FastAPI app with mocked RAG service dependency."""
    from app.main import create_app
    from app.api.dependencies import get_rag_service

    app = create_app()
    
    # Override the dependency BEFORE creating test client
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def app_with_mocked_ingestion(mock_ingestion_service):
    """Provide FastAPI app with mocked ingestion service dependency."""
    from app.main import create_app
    from app.api.dependencies import get_ingestion_service

    app = create_app()
    
    # Override the dependency BEFORE creating test client
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def app_with_mocked_retrieval(mock_retrieval_service):
    """Provide FastAPI app with mocked retrieval service dependency."""
    from app.main import create_app
    from app.api.dependencies import get_retrieval_service

    app = create_app()
    
    # Override the dependency BEFORE creating test client
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def app_with_mocked_documents(mock_ingestion_service, mock_retrieval_service):
    """Provide FastAPI app with both services mocked for document tests."""
    from app.main import create_app
    from app.api.dependencies import get_ingestion_service, get_retrieval_service

    app = create_app()
    
    # Override both dependencies
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def app_with_both_mocks(mock_rag_service, mock_ingestion_service):
    """Provide FastAPI app with both mocked services."""
    from app.main import create_app
    from app.api.dependencies import get_rag_service, get_ingestion_service

    app = create_app()
    
    # Override both dependencies
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()


# ============================================================================
# Windows-specific fixtures (Phase 1: ChromaDB file locking fixes)
# ============================================================================

@pytest.fixture
def temp_dir_windows_safe():
    """
    Provide temporary directory with Windows-safe cleanup.
    
    On Windows, ChromaDB maintains SQLite file handles and binary index files
    that aren't released immediately, preventing pytest from cleaning up
    temporary directories. This fixture handles Windows file locking by:
    1. Using garbage collection to close file handles
    2. Adding a brief delay for file handles to release
    3. Using ignore_errors=True for robust cleanup
    
    On Unix-like systems, uses standard TemporaryDirectory context manager.
    """
    import platform
    import tempfile
    import shutil
    import atexit
    import gc
    
    if platform.system() == "Windows":
        # Windows-specific handling for ChromaDB file locking
        tmpdir = tempfile.mkdtemp()
        
        def cleanup():
            gc.collect()  # Force garbage collection to close file handles
            import time
            time.sleep(0.1)  # Brief delay for file handles to release
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass
        
        # Register cleanup with atexit as backup
        atexit.register(cleanup)
        yield tmpdir
        
        # Attempt immediate cleanup
        cleanup()
    else:
        # Unix-like systems (Linux, macOS)
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
