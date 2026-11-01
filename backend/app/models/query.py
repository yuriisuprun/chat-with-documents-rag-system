"""
Query model for storing Q&A history.

Tracks questions asked, answers generated, and performance metrics.
"""

from sqlalchemy import String, Text, Float, Boolean, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedMixin


# Association table for many-to-many relationship between queries and documents
query_documents = Table(
    "query_documents",
    Base.metadata,
    Column("query_id", String(36), ForeignKey("queries.id"), primary_key=True),
    Column("document_id", String(36), ForeignKey("documents.id"), primary_key=True),
)


class Query(Base, TimestampedMixin):
    """
    Query/Q&A record stored in database.

    Tracks user questions, AI-generated answers, and performance metrics.
    """

    __tablename__ = "queries"

    # ========================================================================
    # Primary Key
    # ========================================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True, doc="UUID")

    # ========================================================================
    # Query Content
    # ========================================================================
    query_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User question/query",
    )

    query_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Length of query text",
    )

    # ========================================================================
    # Answer Content
    # ========================================================================
    answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="AI-generated answer",
    )

    answer_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Length of answer text",
    )

    # ========================================================================
    # Performance Metrics
    # ========================================================================
    retrieval_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Time to retrieve context in milliseconds",
    )

    generation_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Time to generate answer in milliseconds",
    )

    total_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Total end-to-end time in milliseconds",
    )

    # ========================================================================
    # Context Quality
    # ========================================================================
    context_sufficient: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="Whether context was sufficient to answer",
    )

    retrieval_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of chunks retrieved",
    )

    average_similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Average similarity score of retrieved chunks",
    )

    # ========================================================================
    # Metadata
    # ========================================================================
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sessions.id"),
        nullable=True,
        doc="User session ID",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of client",
    )

    user_feedback: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="User feedback: helpful, not_helpful, neutral",
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    documents = relationship(
        "Document",
        secondary=query_documents,
        back_populates="queries",
    )

    session = relationship("Session", back_populates="queries")

    def __repr__(self) -> str:
        """String representation of query."""
        return f"<Query(id={self.id!r}, query={self.query_text[:50]!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "query_text": self.query_text,
            "answer_text": self.answer_text,
            "retrieval_time_ms": self.retrieval_time_ms,
            "generation_time_ms": self.generation_time_ms,
            "total_time_ms": self.total_time_ms,
            "context_sufficient": self.context_sufficient,
            "retrieval_count": self.retrieval_count,
            "average_similarity_score": self.average_similarity_score,
            "user_feedback": self.user_feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
