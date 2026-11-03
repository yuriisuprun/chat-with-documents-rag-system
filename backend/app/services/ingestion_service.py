"""
Document ingestion service.

Orchestrates the complete PDF ingestion pipeline:
1. Validation
2. Extraction
3. Chunking
4. Metadata generation
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List

from app.core.exceptions import EmptyDocumentException
from app.core.logging import get_logger
from app.infrastructure.pdf.chunker import PDFChunker
from app.infrastructure.pdf.extractor import PDFExtractor
from app.infrastructure.pdf.models import Chunk, DocumentMetadata
from app.infrastructure.pdf.validators import validate_pdf_file

logger = get_logger(__name__)


class IngestionService:
    """Service for ingesting and processing PDF documents."""

    def __init__(self):
        """Initialize ingestion service with dependencies."""
        self.extractor = PDFExtractor()
        self.chunker = PDFChunker()

    def ingest_pdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Complete ingestion pipeline for a PDF document.

        Steps:
        1. Validate PDF file (size, signature, readability)
        2. Extract text page-by-page
        3. Chunk extracted text with page preservation
        4. Generate metadata

        Args:
            file_path: Path to uploaded PDF file

        Returns:
            Dictionary containing:
            - document_id: UUID for document
            - filename: Original filename
            - document_metadata: DocumentMetadata object
            - chunks: List of Chunk objects
            - chunk_count: Number of chunks created
            - page_count: Number of pages

        Raises:
            Various validation/processing exceptions

        Example:
            >>> result = service.ingest_pdf(Path("document.pdf"))
            >>> print(f"Created {result['chunk_count']} chunks")
        """
        logger.info(f"Starting ingestion of {file_path.name}")

        # Step 1: Validate PDF
        logger.debug("Step 1: Validating PDF file")
        validation_result = validate_pdf_file(file_path)
        file_hash = validation_result["file_hash"]
        filename = validation_result["filename"]

        # Generate document ID
        document_id = str(uuid.uuid4())
        logger.debug(f"Generated document ID: {document_id}")

        # Step 2: Extract text
        logger.debug("Step 2: Extracting text from PDF")
        extraction_result = self.extractor.extract_text(file_path)
        pages = extraction_result["pages"]
        page_count = extraction_result["page_count"]
        has_extractable_text = extraction_result["has_extractable_text"]
        total_text_length = extraction_result["total_text_length"]

        # Check if document has extractable text
        if not has_extractable_text:
            logger.warning(f"No extractable text found in {filename}")
            raise EmptyDocumentException(filename)

        # Step 3: Chunk text
        logger.debug("Step 3: Chunking extracted text")
        chunks = self.chunker.chunk_extracted_pages(pages, document_id, filename)

        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            raise EmptyDocumentException(filename)

        chunk_count = len(chunks)

        # Step 4: Generate metadata
        logger.debug("Step 4: Generating document metadata")
        document_metadata = DocumentMetadata(
            document_id=document_id,
            filename=filename,
            sha256=file_hash,
            page_count=page_count,
            chunk_count=chunk_count,
            embedding_model=str(None),  # Will be set during embedding (Phase 3)
            total_text_length=total_text_length,
        )

        logger.info(
            f"Successfully ingested {filename}: "
            f"{page_count} pages, {chunk_count} chunks"
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "document_metadata": document_metadata,
            "chunks": chunks,
            "chunk_count": chunk_count,
            "page_count": page_count,
        }

    def validate_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate document without full ingestion.

        Checks size, signature, and that text is extractable.

        Args:
            file_path: Path to PDF file

        Returns:
            Validation result dictionary with keys:
            - is_valid: Boolean indicating validation success
            - filename: Original filename
            - file_size: Size in bytes
            - file_hash: SHA256 hash
            - page_count: Number of pages
            - has_extractable_text: Whether text can be extracted

        Raises:
            Various validation exceptions

        Example:
            >>> result = service.validate_document(Path("doc.pdf"))
            >>> print(f"Valid: {result['is_valid']}, Pages: {result['page_count']}")
        """
        logger.debug(f"Validating document: {file_path.name}")

        # Validate file
        validation_result = validate_pdf_file(file_path)

        # Check if extractable
        has_extractable_text = self.extractor.validate_extractable_text(file_path)

        if not has_extractable_text:
            raise EmptyDocumentException(file_path.name)

        page_count = self.extractor.get_page_count(file_path)

        return {
            "is_valid": True,
            "filename": validation_result["filename"],
            "file_size": validation_result["file_size"],
            "file_hash": validation_result["file_hash"],
            "page_count": page_count,
            "has_extractable_text": has_extractable_text,
        }
