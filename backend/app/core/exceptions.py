"""
Custom exception classes for the application.

Follows clean architecture pattern with specific, meaningful exceptions
for different layers of the application.
"""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        """Initialize exception with message and error code."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# ============================================================================
# Validation Exceptions
# ============================================================================


class ValidationException(ApplicationException):
    """Raised when input validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code)


class FileSizeException(ValidationException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, size: int, max_size: int):
        message = f"File size {size} bytes exceeds maximum {max_size} bytes"
        super().__init__(message, "FILE_TOO_LARGE")


class InvalidFileTypeException(ValidationException):
    """Raised when uploaded file is not a valid PDF."""

    def __init__(self, filename: str):
        message = f"File '{filename}' is not a valid PDF"
        super().__init__(message, "INVALID_FILE_TYPE")


class InvalidPDFException(ValidationException):
    """Raised when PDF is corrupted or unreadable."""

    def __init__(self, filename: str, reason: str):
        message = f"Invalid PDF '{filename}': {reason}"
        super().__init__(message, "INVALID_PDF")


class PDFPageCountException(ValidationException):
    """Raised when PDF exceeds maximum page count."""

    def __init__(self, page_count: int, max_pages: int):
        message = f"PDF has {page_count} pages, maximum is {max_pages}"
        super().__init__(message, "PDF_PAGE_COUNT_EXCEEDED")


class EmptyDocumentException(ValidationException):
    """Raised when document has no extractable content."""

    def __init__(self, filename: str):
        message = f"Document '{filename}' has no extractable text"
        super().__init__(message, "EMPTY_DOCUMENT")


# ============================================================================
# Document Processing Exceptions
# ============================================================================


class DocumentProcessingException(ApplicationException):
    """Raised when document processing fails."""

    def __init__(self, message: str, error_code: str = "PROCESSING_ERROR"):
        super().__init__(message, error_code)


class PDFExtractionException(DocumentProcessingException):
    """Raised when PDF text extraction fails."""

    def __init__(self, filename: str, reason: str):
        message = f"Failed to extract text from '{filename}': {reason}"
        super().__init__(message, "PDF_EXTRACTION_ERROR")


class ChunkingException(DocumentProcessingException):
    """Raised when text chunking fails."""

    def __init__(self, reason: str):
        message = f"Text chunking failed: {reason}"
        super().__init__(message, "CHUNKING_ERROR")


class EmbeddingException(DocumentProcessingException):
    """Raised when embedding generation fails."""

    def __init__(self, reason: str):
        message = f"Embedding generation failed: {reason}"
        super().__init__(message, "EMBEDDING_ERROR")


# ============================================================================
# Vector Store Exceptions
# ============================================================================


class VectorStoreException(ApplicationException):
    """Raised when vector store operation fails."""

    def __init__(self, message: str, error_code: str = "VECTOR_STORE_ERROR"):
        super().__init__(message, error_code)


class IndexingException(VectorStoreException):
    """Raised when indexing fails."""

    def __init__(self, reason: str):
        message = f"Indexing failed: {reason}"
        super().__init__(message, "INDEXING_ERROR")


class RetrievalException(VectorStoreException):
    """Raised when retrieval fails."""

    def __init__(self, reason: str):
        message = f"Retrieval failed: {reason}"
        super().__init__(message, "RETRIEVAL_ERROR")


# ============================================================================
# LLM Exceptions
# ============================================================================


class LLMException(ApplicationException):
    """Raised when LLM operation fails."""

    def __init__(self, message: str, error_code: str = "LLM_ERROR"):
        super().__init__(message, error_code)


class LLMTimeoutException(LLMException):
    """Raised when LLM request times out."""

    def __init__(self, timeout_seconds: int):
        message = f"LLM request timed out after {timeout_seconds} seconds"
        super().__init__(message, "LLM_TIMEOUT")


class LLMUnavailableException(LLMException):
    """Raised when LLM service is unavailable."""

    def __init__(self, provider: str, reason: str):
        message = f"LLM provider '{provider}' unavailable: {reason}"
        super().__init__(message, "LLM_UNAVAILABLE")


# ============================================================================
# Database Exceptions
# ============================================================================


class DatabaseException(ApplicationException):
    """Raised when database operation fails."""

    def __init__(self, message: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, error_code)


class DocumentNotFoundException(DatabaseException):
    """Raised when document is not found in database."""

    def __init__(self, document_id: str):
        message = f"Document '{document_id}' not found"
        super().__init__(message, "DOCUMENT_NOT_FOUND")


class DuplicateDocumentException(DatabaseException):
    """Raised when attempting to ingest duplicate document."""

    def __init__(self, filename: str):
        message = f"Document '{filename}' already indexed"
        super().__init__(message, "DUPLICATE_DOCUMENT")


# ============================================================================
# RAG Exceptions
# ============================================================================


class RAGException(ApplicationException):
    """Raised when RAG pipeline fails."""

    def __init__(self, message: str, error_code: str = "RAG_ERROR"):
        super().__init__(message, error_code)


class InsufficientContextException(RAGException):
    """Raised when retrieved context is insufficient to answer question."""

    def __init__(self, query: str):
        message = f"Insufficient context to answer: '{query}'"
        super().__init__(message, "INSUFFICIENT_CONTEXT")


# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigurationException(ApplicationException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, error_code: str = "CONFIG_ERROR"):
        super().__init__(message, error_code)
