"""
Dependency injection container.

Centralizes creation and configuration of application services.
Will be expanded as services are implemented.
"""

from functools import lru_cache

from app.core.config import Settings
from app.infrastructure.embeddings.huggingface_provider import (
    HuggingFaceEmbeddingProvider,
)
from app.infrastructure.vectorstore.chroma import ChromaVectorStore
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService
from app.services.rag_service import RAGService


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns:
        Settings: Application configuration
    """
    from app.core.config import settings
    return settings


@lru_cache(maxsize=1)
def get_embedding_provider() -> HuggingFaceEmbeddingProvider:
    """
    Get embedding provider (singleton).
    
    Cached to avoid multiple initializations and HuggingFace lock contention.

    Returns:
        HuggingFaceEmbeddingProvider: Configured embedding provider
    """
    return HuggingFaceEmbeddingProvider()


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    """
    Get vector store (singleton).
    
    Cached to maintain single ChromaDB connection.

    Returns:
        ChromaVectorStore: Configured vector store
    """
    return ChromaVectorStore()


def get_ingestion_service() -> IngestionService:
    """
    Get ingestion service for document processing.

    Returns:
        IngestionService: Configured ingestion service
    """
    return IngestionService()


def get_retrieval_service() -> RetrievalService:
    """
    Get retrieval service for semantic search.
    
    Uses singleton embedding provider and vector store to avoid lock contention.

    Returns:
        RetrievalService: Configured retrieval service
    """
    return RetrievalService(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


def get_rag_service() -> RAGService:
    """
    Get RAG service for question answering.

    Returns:
        RAGService: Configured RAG service
    """
    return RAGService()


# Additional dependencies will be added as services are implemented:
# - get_db() for database session
# - get_llm() for LLM provider
# - etc.
