"""
Document model for storing PDF metadata.

Tracks document information including file details, processing status, and statistics.
"""

from sqlalchemy import String, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedMixin


class Document(Base, TimestampedMixin):
    """
    Document metadata stored in database.

    Tracks uploaded PDF documents, their processing status, and statistics.
    """

    __tablename__ = "documents"

    # ========================================================================
    # Primary Key
    # ========================================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True, doc="UUID")

    # ========================================================================
    # File Information
    # ========================================================================
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original filename",
    )

    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="Path to uploaded file",
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="File size in bytes",
    )

    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        doc="SHA-256 hash of file content for deduplication",
    )

    # ========================================================================
    # Document Content Statistics
    # ========================================================================
    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of pages in PDF",
    )

    text_length: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        doc="Total extracted text length",
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of text chunks created",
    )

    # ========================================================================
    # Processing Status
    # ========================================================================
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        doc="Status: pending, processing, indexed, failed",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if processing failed",
    )

    # ========================================================================
    # Model Configuration
    # ========================================================================
    embedding_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Embedding model used for this document",
    )

    # ========================================================================
    # Vector Store References
    # ========================================================================
    vector_store_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        doc="Reference to vector store collection/index",
    )

    # ========================================================================
    # Analytics
    # ========================================================================
    query_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Number of queries matching this document",
    )

    access_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Number of times document was accessed",
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    queries = relationship("Query", back_populates="documents", secondary="query_documents")

    def __repr__(self) -> str:
        """String representation of document."""
        return f"<Document(id={self.id!r}, filename={self.filename!r}, status={self.status!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "embedding_model": self.embedding_model,
            "query_count": self.query_count,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
