"""
Database service for high-level database operations.

Manages document metadata, query history, and analytics.
"""

import hashlib
import time
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.repositories import (
    DocumentRepository,
    QueryRepository,
    SessionRepository,
)
from app.models.document import Document

logger = get_logger(__name__)


class DatabaseService:
    """Service for database operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.documents = DocumentRepository(session)
        self.queries = QueryRepository(session)
        self.sessions = SessionRepository(session)

    # ========================================================================
    # Document Operations
    # ========================================================================

    def register_document(
        self,
        filename: str,
        file_path: str,
        page_count: int,
        chunk_count: int,
        embedding_model: str,
    ) -> Document:
        """
        Register a new document in database.

        Args:
            filename: Document filename
            file_path: Path to uploaded file
            page_count: Number of pages
            chunk_count: Number of chunks
            embedding_model: Embedding model used

        Returns:
            Created Document object
        """
        # Calculate file size and hash
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size

        # Calculate SHA256 hash
        sha256_hash = self._calculate_sha256(file_path)

        # Check for duplicates
        existing = self.documents.get_by_hash(sha256_hash)
        if existing:
            logger.warning(f"Duplicate document detected: {existing.id}")
            raise ValueError(f"Document already indexed: {existing.filename}")

        # Create document record
        document_id = str(uuid4())
        document = self.documents.create(
            document_id=document_id,
            filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            sha256_hash=sha256_hash,
            page_count=page_count,
            chunk_count=chunk_count,
            embedding_model=embedding_model,
        )

        self.session.commit()
        logger.info(f"Registered document: {document_id}")
        return document

    def mark_document_indexed(self, document_id: str):
        """Mark document as successfully indexed."""
        self.documents.update_status(document_id, "indexed")
        self.session.commit()
        logger.info(f"Marked document {document_id} as indexed")

    def mark_document_failed(self, document_id: str, error: str):
        """Mark document as failed with error message."""
        self.documents.update_status(document_id, "failed", error)
        self.session.commit()
        logger.error(f"Marked document {document_id} as failed: {error}")

    def get_document(self, document_id: str) -> Document | None:
        """Get document by ID."""
        return self.documents.get_by_id(document_id)

    def delete_document(self, document_id: str) -> bool:
        """Delete document and associated data."""
        result = self.documents.delete(document_id)
        self.session.commit()
        return result

    def list_documents(self, limit: int = 100, offset: int = 0) -> list[Document]:
        """List all documents."""
        return self.documents.get_all(limit=limit, offset=offset)

    def get_document_stats(self) -> dict:
        """Get document statistics."""
        return self.documents.get_stats()

    # ========================================================================
    # Query Operations
    # ========================================================================

    def record_query(
        self,
        query_text: str,
        answer_text: str,
        retrieval_time_ms: float,
        generation_time_ms: float,
        context_sufficient: bool,
        retrieval_count: int,
        average_similarity_score: float,
        session_id: str | None = None,
        ip_address: str | None = None,
    ) -> str:
        """
        Record a query and answer in database.

        Args:
            query_text: User question
            answer_text: Generated answer
            retrieval_time_ms: Time to retrieve context
            generation_time_ms: Time to generate answer
            context_sufficient: Whether context was sufficient
            retrieval_count: Number of chunks retrieved
            average_similarity_score: Average similarity score
            session_id: Optional session ID
            ip_address: Optional client IP

        Returns:
            Query ID
        """
        query = self.queries.create(
            query_text=query_text,
            answer_text=answer_text,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            context_sufficient=context_sufficient,
            retrieval_count=retrieval_count,
            average_similarity_score=average_similarity_score,
            session_id=session_id,
            ip_address=ip_address,
        )

        self.session.commit()
        logger.info(f"Recorded query: {query.id}")
        return query.id

    def add_query_feedback(self, query_id: str, feedback: str):
        """Add user feedback to a query."""
        self.queries.add_user_feedback(query_id, feedback)
        self.session.commit()
        logger.info(f"Added feedback to query {query_id}")

    def get_recent_queries(self, hours: int = 24, limit: int = 50) -> list:
        """Get recent queries."""
        return self.queries.get_recent(hours=hours, limit=limit)

    def get_query_stats(self) -> dict:
        """Get query statistics."""
        return self.queries.get_stats()

    # ========================================================================
    # Session Operations
    # ========================================================================

    def create_session(
        self,
        ip_address: str,
        user_agent: str | None = None,
        session_name: str | None = None,
    ) -> str:
        """Create new session."""
        session_record = self.sessions.create(
            ip_address=ip_address,
            user_agent=user_agent,
            session_name=session_name,
        )
        self.session.commit()
        logger.info(f"Created session: {session_record.id}")
        return session_record.id

    def get_session(self, session_id: str):
        """Get session by ID."""
        return self.sessions.get_by_id(session_id)

    def get_session_stats(self) -> dict:
        """Get session statistics."""
        return self.sessions.get_stats()

    # ========================================================================
    # Analytics
    # ========================================================================

    def get_overall_stats(self) -> dict:
        """Get overall system statistics."""
        docs = self.documents.get_stats()
        queries = self.queries.get_stats()
        sessions = self.sessions.get_stats()

        return {
            "documents": docs,
            "queries": queries,
            "sessions": sessions,
            "timestamp": time.time(),
        }

    def get_trending_queries(self, limit: int = 10) -> list[dict]:
        """Get trending queries (most accessed documents)."""
        # This would require additional implementation
        # For now, return most recent queries
        queries = self.queries.get_recent(hours=7, limit=limit)
        return [q.to_dict() for q in queries]

    # ========================================================================
    # Utilities
    # ========================================================================

    @staticmethod
    def _calculate_sha256(file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def commit(self):
        """Commit session changes."""
        self.session.commit()

    def rollback(self):
        """Rollback session changes."""
        self.session.rollback()
