"""
Repository classes for database access.

Provides clean data access layer for models.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document import Document
from app.models.query import Query, query_documents
from app.models.session import Session as SessionModel

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document database operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def create(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        sha256_hash: str,
        page_count: int,
        chunk_count: int,
        embedding_model: str,
    ) -> Document:
        """Create new document record."""
        document = Document(
            id=document_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            sha256_hash=sha256_hash,
            page_count=page_count,
            chunk_count=chunk_count,
            embedding_model=embedding_model,
            status="pending",
        )
        self.session.add(document)
        self.session.flush()
        logger.info(f"Created document record: {document_id}")
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        """Get document by ID."""
        return self.session.query(Document).filter(Document.id == document_id).first()

    def get_by_hash(self, sha256_hash: str) -> Document | None:
        """Get document by SHA256 hash (check for duplicates)."""
        return self.session.query(Document).filter(
            Document.sha256_hash == sha256_hash
        ).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[Document]:
        """Get all documents with pagination."""
        return (
            self.session.query(Document)
            .order_by(desc(Document.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_status(self, status: str) -> list[Document]:
        """Get documents by status."""
        return self.session.query(Document).filter(Document.status == status).all()

    def update_status(self, document_id: str, status: str, error_message: str | None = None):
        """Update document status."""
        document = self.get_by_id(document_id)
        if document:
            document.status = status
            document.error_message = error_message
            self.session.flush()
            logger.info(f"Updated document {document_id} status to {status}")

    def update_stats(
        self,
        document_id: str,
        text_length: int,
        chunk_count: int,
    ):
        """Update document statistics."""
        document = self.get_by_id(document_id)
        if document:
            document.text_length = text_length
            document.chunk_count = chunk_count
            self.session.flush()

    def delete(self, document_id: str) -> bool:
        """Delete document record."""
        document = self.get_by_id(document_id)
        if document:
            self.session.delete(document)
            self.session.flush()
            logger.info(f"Deleted document: {document_id}")
            return True
        return False

    def get_stats(self) -> dict:
        """Get database statistics."""
        total = self.session.query(func.count(Document.id)).scalar()
        indexed = self.session.query(func.count(Document.id)).filter(
            Document.status == "indexed"
        ).scalar()
        failed = self.session.query(func.count(Document.id)).filter(
            Document.status == "failed"
        ).scalar()
        total_chunks = self.session.query(func.sum(Document.chunk_count)).scalar() or 0

        return {
            "total_documents": total,
            "indexed_documents": indexed,
            "failed_documents": failed,
            "total_chunks": total_chunks,
        }


class QueryRepository:
    """Repository for query database operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def create(
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
    ) -> Query:
        """Create new query record."""
        query = Query(
            id=str(uuid4()),
            query_text=query_text,
            query_length=len(query_text),
            answer_text=answer_text,
            answer_length=len(answer_text),
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            total_time_ms=retrieval_time_ms + generation_time_ms,
            context_sufficient=context_sufficient,
            retrieval_count=retrieval_count,
            average_similarity_score=average_similarity_score,
            session_id=session_id,
            ip_address=ip_address,
        )
        self.session.add(query)
        self.session.flush()
        logger.info(f"Created query record: {query.id}")
        return query

    def get_by_id(self, query_id: str) -> Query | None:
        """Get query by ID."""
        return self.session.query(Query).filter(Query.id == query_id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[Query]:
        """Get all queries with pagination."""
        return (
            self.session.query(Query)
            .order_by(desc(Query.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_session(self, session_id: str) -> list[Query]:
        """Get queries for a session."""
        return self.session.query(Query).filter(Query.session_id == session_id).all()

    def get_recent(self, hours: int = 24, limit: int = 50) -> list[Query]:
        """Get recent queries from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.session.query(Query)
            .filter(Query.created_at >= cutoff)
            .order_by(desc(Query.created_at))
            .limit(limit)
            .all()
        )

    def add_user_feedback(self, query_id: str, feedback: str):
        """Add user feedback to a query."""
        query = self.get_by_id(query_id)
        if query:
            query.user_feedback = feedback
            self.session.flush()
            logger.info(f"Added feedback to query {query_id}: {feedback}")

    def get_stats(self) -> dict:
        """Get query statistics."""
        total = self.session.query(func.count(Query.id)).scalar()
        avg_retrieval = self.session.query(
            func.avg(Query.retrieval_time_ms)
        ).scalar() or 0
        avg_generation = self.session.query(
            func.avg(Query.generation_time_ms)
        ).scalar() or 0
        avg_total = self.session.query(func.avg(Query.total_time_ms)).scalar() or 0

        sufficient = self.session.query(func.count(Query.id)).filter(
            Query.context_sufficient == True
        ).scalar()

        return {
            "total_queries": total,
            "avg_retrieval_time_ms": avg_retrieval,
            "avg_generation_time_ms": avg_generation,
            "avg_total_time_ms": avg_total,
            "context_sufficient_count": sufficient,
            "context_sufficient_percentage": (
                (sufficient / total * 100) if total > 0 else 0
            ),
        }


class SessionRepository:
    """Repository for session database operations."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def create(
        self,
        ip_address: str,
        user_agent: str | None = None,
        session_name: str | None = None,
    ) -> SessionModel:
        """Create new session record."""
        session_record = SessionModel(
            id=str(uuid4()),
            ip_address=ip_address,
            user_agent=user_agent,
            session_name=session_name,
        )
        self.session.add(session_record)
        self.session.flush()
        logger.info(f"Created session: {session_record.id}")
        return session_record

    def get_by_id(self, session_id: str) -> SessionModel | None:
        """Get session by ID."""
        return self.session.query(SessionModel).filter(SessionModel.id == session_id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[SessionModel]:
        """Get all sessions with pagination."""
        return (
            self.session.query(SessionModel)
            .order_by(desc(SessionModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update_stats(
        self,
        session_id: str,
        query_count: int | None = None,
        upload_count: int | None = None,
    ):
        """Update session statistics."""
        session_record = self.get_by_id(session_id)
        if session_record:
            if query_count is not None:
                session_record.query_count = query_count
            if upload_count is not None:
                session_record.document_upload_count = upload_count
            self.session.flush()

    def get_stats(self) -> dict:
        """Get session statistics."""
        total = self.session.query(func.count(SessionModel.id)).scalar()
        avg_queries = self.session.query(
            func.avg(SessionModel.query_count)
        ).scalar() or 0

        return {
            "total_sessions": total,
            "avg_queries_per_session": avg_queries,
        }
