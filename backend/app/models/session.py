"""
Session model for tracking user sessions.

Records user interaction sessions, including queries and metadata.
"""

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedMixin


class Session(Base, TimestampedMixin):
    """
    User session tracking.

    Records user sessions including session metadata and associated queries.
    """

    __tablename__ = "sessions"

    # ========================================================================
    # Primary Key
    # ========================================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True, doc="UUID")

    # ========================================================================
    # Session Information
    # ========================================================================
    session_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional user-friendly session name",
    )

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        doc="Client IP address",
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        doc="Client user agent string",
    )

    # ========================================================================
    # Session Statistics
    # ========================================================================
    query_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Number of queries in this session",
    )

    document_upload_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Number of documents uploaded in this session",
    )

    # ========================================================================
    # Metrics
    # ========================================================================
    total_time_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="Total session duration in seconds",
    )

    average_query_time_ms: Mapped[float | None] = mapped_column(
        nullable=True,
        doc="Average time per query in milliseconds",
    )

    # ========================================================================
    # Notes
    # ========================================================================
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Session notes or feedback from user",
    )

    # ========================================================================
    # Relationships
    # ========================================================================
    queries = relationship("Query", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of session."""
        return f"<Session(id={self.id!r}, ip={self.ip_address!r}, queries={self.query_count})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_name": self.session_name,
            "ip_address": self.ip_address,
            "query_count": self.query_count,
            "document_upload_count": self.document_upload_count,
            "total_time_seconds": self.total_time_seconds,
            "average_query_time_ms": self.average_query_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
