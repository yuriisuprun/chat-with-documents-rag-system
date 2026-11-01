"""
Data models for PDF processing.

Represents chunks and metadata extracted from PDFs.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Chunk:
    """Represents a text chunk extracted from a PDF."""

    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    text_length: int

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"Chunk(id={self.chunk_id}, "
            f"page={self.page_number}, "
            f"size={self.text_length})"
        )


@dataclass
class ChunkMetadata:
    """Metadata associated with a chunk for retrieval."""

    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int

    def to_dict(self) -> dict:
        """Convert to dictionary for ChromaDB metadata."""
        return asdict(self)


@dataclass
class DocumentMetadata:
    """Metadata about a processed PDF document."""

    document_id: str
    filename: str
    sha256: str
    page_count: int
    chunk_count: int
    embedding_model: str
    total_text_length: int

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return asdict(self)
