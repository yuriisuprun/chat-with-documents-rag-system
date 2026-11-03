"""
Dependency injection container.

Centralizes creation and configuration of application services.
Will be expanded as services are implemented.
"""

from functools import lru_cache

from app.core.config import Settings
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
    return settings


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

    Returns:
        RetrievalService: Configured retrieval service
    """
    return RetrievalService()


def get_rag_service() -> RAGService:
    """
    Get RAG service for question answering.

    Returns:
        RAGService: Configured RAG service
    """
    return RAGService()


# Additional dependencies will be added as services are implemented:
# - get_db() for database session
# - get_embeddings() for embedding provider
# - get_llm() for LLM provider
# - get_vector_store() for ChromaDB
# - etc.
