"""
Configuration management using Pydantic Settings.

Centralized environment-based configuration following 12-factor app principles.
All settings are read from environment variables with sensible defaults.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    environment: Literal["development", "testing", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_port: int = 8501
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    reload: bool = True

    # ========================================================================
    # File Upload Settings
    # ========================================================================
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    max_pdf_pages: int = 100
    upload_dir: str = "./data/uploads"

    # ========================================================================
    # PDF Processing Settings
    # ========================================================================
    pdf_extract_text: bool = True
    pdf_extract_ocr: bool = False  # Not implemented in MVP

    # ========================================================================
    # Chunking Settings
    # ========================================================================
    chunk_size: int = 800
    chunk_overlap: int = 120

    # ========================================================================
    # Embeddings Settings
    # ========================================================================
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: Literal["cpu", "cuda"] = "cpu"
    embedding_normalize: bool = True

    # ========================================================================
    # Vector Store Settings
    # ========================================================================
    chromadb_persist_dir: str = "./data/chroma"
    chromadb_collection_name: str = "documents"

    # ========================================================================
    # LLM Settings
    # ========================================================================
    llm_provider: Literal["ollama", "openai"] = "ollama"

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_temperature: float = 0.3
    ollama_top_p: float = 0.9
    ollama_timeout: int = 120

    # OpenAI settings (optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3

    # ========================================================================
    # Retrieval Settings
    # ========================================================================
    retrieval_top_k: int = 4
    retrieval_similarity_threshold: float = 0.0

    # ========================================================================
    # Database Settings
    # ========================================================================
    database_url: str = "sqlite:///./data/app.db"

    # ========================================================================
    # Security Settings
    # ========================================================================
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8501"
    
    # API key authentication (Phase 8)
    api_key_enabled: bool = False
    api_key: str = ""
    
    # Rate limiting (Phase 8)
    rate_limit_enabled: bool = True
    rate_limit_global: int = 100  # requests per minute
    rate_limit_upload: int = 10   # requests per minute
    rate_limit_chat: int = 30     # requests per minute
    
    # Input validation (Phase 8)
    max_query_length: int = 500
    max_document_id_length: int = 36
    
    # Security headers (Phase 8)
    enable_security_headers: bool = True
    enable_hsts: bool = False  # Only true in production

    # ========================================================================
    # RAG Settings
    # ========================================================================
    rag_check_sufficiency: bool = True
    rag_max_context_tokens: int = 2000

    # ========================================================================
    # Logging Settings
    # ========================================================================
    log_json: bool = False

    # ========================================================================
    # Testing
    # ========================================================================
    test_mode: bool = False

    # ========================================================================
    # Derived Properties (computed at runtime)
    # ========================================================================
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_directory(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir)

    @property
    def chroma_directory(self) -> Path:
        """Get ChromaDB directory as Path object."""
        return Path(self.chromadb_persist_dir)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.environment == "testing"

    def __repr__(self) -> str:
        """Return a safe string representation without sensitive values."""
        return (
            f"Settings(environment={self.environment}, "
            f"api_host={self.api_host}, "
            f"api_port={self.api_port}, "
            f"llm_provider={self.llm_provider}, "
            f"embedding_model={self.embedding_model})"
        )


# Global settings instance
settings = Settings()
