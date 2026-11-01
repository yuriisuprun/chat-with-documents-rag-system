"""
Base abstraction for vector store implementations.

Defines interface for vector database operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    """A retrieved chunk with similarity score."""

    chunk_id: str
    text: str
    similarity_score: float
    metadata: dict


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add_chunks(
        self, chunk_ids: list[str], texts: list[str], embeddings: list[list[float]], metadata_list: list[dict]
    ) -> None:
        """
        Add chunks to vector store.

        Args:
            chunk_ids: List of chunk IDs
            texts: List of chunk texts
            embeddings: List of embedding vectors
            metadata_list: List of metadata dicts for each chunk
        """
        pass

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 4, filter_dict: dict | None = None
    ) -> list[RetrievedChunk]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            filter_dict: Optional metadata filter

        Returns:
            List of retrieved chunks with similarity scores
        """
        pass

    @abstractmethod
    def delete_chunks(self, chunk_ids: list[str]) -> None:
        """
        Delete chunks from vector store.

        Args:
            chunk_ids: List of chunk IDs to delete
        """
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID
        """
        pass

    @abstractmethod
    def get_collection_size(self) -> int:
        """
        Get number of chunks in collection.

        Returns:
            Number of chunks
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from vector store."""
        pass
