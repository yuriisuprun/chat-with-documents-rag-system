"""
Unit tests for database service.

Tests document registration, query recording, and analytics.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Database
from app.models.base import Base
from app.services.database_service import DatabaseService


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@pytest.fixture
def db_service(test_db):
    """Create database service with test database."""
    return DatabaseService(test_db)


class TestDocumentRepository:
    """Test document registration and management."""

    def test_register_document(self, db_service, tmp_path):
        """Test registering a document."""
        # Create temporary file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")

        # Register document
        doc = db_service.register_document(
            filename="test.pdf",
            file_path=str(test_file),
            page_count=5,
            chunk_count=10,
            embedding_model="test-model",
        )

        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.page_count == 5
        assert doc.chunk_count == 10
        assert doc.status == "pending"  # Initially pending, then indexed after processing

    def test_duplicate_document_detection(self, db_service, tmp_path):
        """Test that duplicate documents are detected."""
        # Create and register first document
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")

        doc1 = db_service.register_document(
            filename="test.pdf",
            file_path=str(test_file),
            page_count=5,
            chunk_count=10,
            embedding_model="test-model",
        )

        # Try to register duplicate
        with pytest.raises(ValueError) as exc_info:
            db_service.register_document(
                filename="test.pdf",
                file_path=str(test_file),
                page_count=5,
                chunk_count=10,
                embedding_model="test-model",
            )

        assert "already indexed" in str(exc_info.value)

    def test_mark_document_indexed(self, db_service, tmp_path):
        """Test marking document as indexed."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")

        doc = db_service.register_document(
            filename="test.pdf",
            file_path=str(test_file),
            page_count=5,
            chunk_count=10,
            embedding_model="test-model",
        )

        # Initially status should be "pending"
        assert doc.status == "pending"
        
        # Mark as indexed
        db_service.mark_document_indexed(doc.id)
        
        # Verify status changed
        updated_doc = db_service.get_document(doc.id)
        assert updated_doc.status == "indexed"

    def test_list_documents(self, db_service, tmp_path):
        """Test listing documents."""
        # Create multiple documents
        for i in range(3):
            test_file = tmp_path / f"test{i}.pdf"
            test_file.write_bytes(f"PDF content {i}".encode())

            db_service.register_document(
                filename=f"test{i}.pdf",
                file_path=str(test_file),
                page_count=5,
                chunk_count=10,
                embedding_model="test-model",
            )

        # List documents
        docs = db_service.list_documents()
        assert len(docs) == 3

    def test_delete_document(self, db_service, tmp_path):
        """Test deleting a document."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")

        doc = db_service.register_document(
            filename="test.pdf",
            file_path=str(test_file),
            page_count=5,
            chunk_count=10,
            embedding_model="test-model",
        )

        # Delete document
        result = db_service.delete_document(doc.id)
        assert result is True

        # Verify deletion
        deleted = db_service.get_document(doc.id)
        assert deleted is None


class TestQueryRepository:
    """Test query recording and analytics."""

    def test_record_query(self, db_service):
        """Test recording a query."""
        query_id = db_service.record_query(
            query_text="What is AI?",
            answer_text="AI is artificial intelligence.",
            retrieval_time_ms=200.5,
            generation_time_ms=2500.0,
            context_sufficient=True,
            retrieval_count=4,
            average_similarity_score=0.85,
        )

        assert query_id is not None

        # Retrieve and verify
        query = db_service.queries.get_by_id(query_id)
        assert query.query_text == "What is AI?"
        assert query.answer_text == "AI is artificial intelligence."
        assert query.context_sufficient is True

    def test_add_query_feedback(self, db_service):
        """Test adding user feedback to query."""
        query_id = db_service.record_query(
            query_text="Question?",
            answer_text="Answer.",
            retrieval_time_ms=200.0,
            generation_time_ms=2000.0,
            context_sufficient=True,
            retrieval_count=4,
            average_similarity_score=0.9,
        )

        db_service.add_query_feedback(query_id, "helpful")

        query = db_service.queries.get_by_id(query_id)
        assert query.user_feedback == "helpful"

    def test_get_query_stats(self, db_service):
        """Test getting query statistics."""
        # Record multiple queries
        for i in range(3):
            db_service.record_query(
                query_text=f"Question {i}?",
                answer_text=f"Answer {i}.",
                retrieval_time_ms=200.0 + i * 50,
                generation_time_ms=2000.0 + i * 100,
                context_sufficient=i % 2 == 0,
                retrieval_count=4,
                average_similarity_score=0.85 + i * 0.01,
            )

        stats = db_service.get_query_stats()
        assert stats["total_queries"] == 3
        assert stats["avg_retrieval_time_ms"] > 0
        assert stats["avg_generation_time_ms"] > 0


class TestSessionRepository:
    """Test session management."""

    def test_create_session(self, db_service):
        """Test creating a session."""
        session_id = db_service.create_session(
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            session_name="Test Session",
        )

        assert session_id is not None

        # Verify
        session = db_service.get_session(session_id)
        assert session.ip_address == "127.0.0.1"
        assert session.session_name == "Test Session"

    def test_get_session_stats(self, db_service):
        """Test getting session statistics."""
        # Create multiple sessions
        for i in range(2):
            db_service.create_session(
                ip_address=f"127.0.0.{i}",
                user_agent="Mozilla/5.0",
            )

        stats = db_service.get_session_stats()
        assert stats["total_sessions"] == 2


class TestAnalytics:
    """Test analytics and statistics."""

    def test_get_overall_stats(self, db_service, tmp_path):
        """Test getting overall statistics."""
        # Create a document
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content")

        db_service.register_document(
            filename="test.pdf",
            file_path=str(test_file),
            page_count=5,
            chunk_count=10,
            embedding_model="test-model",
        )

        # Record a query
        db_service.record_query(
            query_text="Question?",
            answer_text="Answer.",
            retrieval_time_ms=200.0,
            generation_time_ms=2000.0,
            context_sufficient=True,
            retrieval_count=4,
            average_similarity_score=0.9,
        )

        # Create a session
        db_service.create_session(ip_address="127.0.0.1")

        # Get stats
        stats = db_service.get_overall_stats()
        assert "documents" in stats
        assert "queries" in stats
        assert "sessions" in stats
        assert stats["documents"]["total_documents"] == 1
        assert stats["queries"]["total_queries"] == 1
        assert stats["sessions"]["total_sessions"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
