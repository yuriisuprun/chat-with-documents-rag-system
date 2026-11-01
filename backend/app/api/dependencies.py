"""
Dependency injection container.

Centralizes creation and configuration of application services.
Will be expanded as services are implemented.
"""

from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def get_settings():
    """
    Get application settings (cached).

    Returns:
        Settings: Application configuration
    """
    return settings


# Additional dependencies will be added as services are implemented:
# - get_db() for database session
# - get_embeddings() for embedding provider
# - get_llm() for LLM provider
# - get_vector_store() for ChromaDB
# - etc.
