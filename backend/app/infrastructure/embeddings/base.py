"""
Base abstraction for embedding providers.

Defines interface for different embedding implementations.
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple text strings.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced.

        Returns:
            Dimension of embedding vectors
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name/identifier
        """
        pass
