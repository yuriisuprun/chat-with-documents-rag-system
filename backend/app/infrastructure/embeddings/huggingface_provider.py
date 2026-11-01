"""
HuggingFace Sentence Transformers embedding provider.

Uses sentence-transformers for semantic embeddings.
"""

from typing import Optional

from app.core.config import settings
from app.core.exceptions import EmbeddingException
from app.core.logging import get_logger
from app.infrastructure.embeddings.base import EmbeddingProvider

logger = get_logger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using HuggingFace sentence-transformers."""

    _instance: Optional["HuggingFaceEmbeddingProvider"] = None
    _model = None

    def __new__(cls):
        """Singleton pattern - only one model instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize embedding provider (lazy loading)."""
        if self._initialized:
            return

        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        self.normalize = settings.embedding_normalize
        self._model = None
        self._initialized = True

        logger.debug(
            f"HuggingFaceEmbeddingProvider initialized: "
            f"model={self.model_name}, device={self.device}"
        )

    def _load_model(self):
        """Load model on first use (lazy loading)."""
        if self._model is not None:
            return

        try:
            logger.debug(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )
            logger.info(f"Embedding model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingException(f"Failed to load model {self.model_name}: {str(e)}")

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingException: If embedding fails
        """
        try:
            self._load_model()

            # Embed text
            embedding = self._model.encode(
                text,
                normalize_embeddings=self.normalize,
                convert_to_numpy=False,
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise EmbeddingException(f"Embedding failed: {str(e)}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple text strings.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingException: If embedding fails
        """
        try:
            self._load_model()

            # Embed texts in batch
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=self.normalize,
                convert_to_numpy=False,
                show_progress_bar=False,
            )

            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise EmbeddingException(f"Batch embedding failed: {str(e)}")

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced.

        Returns:
            Dimension of embedding vectors
        """
        try:
            self._load_model()
            return self._model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            raise EmbeddingException(f"Failed to get dimension: {str(e)}")

    def get_model_name(self) -> str:
        """
        Get the name of the embedding model.

        Returns:
            Model name/identifier
        """
        return self.model_name
