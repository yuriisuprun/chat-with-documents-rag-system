"""
Unit tests for document ingestion service.

Tests the complete ingestion pipeline.
"""

import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import EmptyDocumentException
from app.services.ingestion_service import IngestionService


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def ingestion_service():
    """Create ingestion service instance."""
    return IngestionService()


@pytest.fixture
def simple_pdf(temp_dir):
    """Create a simple PDF with text content."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_path = temp_dir / "simple.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        c.drawString(100, 750, "This is a test document")
        c.drawString(100, 730, "It has multiple lines")
        c.drawString(100, 710, "And some content to extract")
        c.showPage()

        c.save()
        return pdf_path
    except ImportError:
        pytest.skip("reportlab not installed")


class TestIngestionService:
    """Test document ingestion service."""

    def test_ingest_pdf_returns_expected_structure(self, ingestion_service, simple_pdf):
        """Test that ingestion returns correct structure."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        required_keys = {
            "document_id",
            "filename",
            "document_metadata",
            "chunks",
            "chunk_count",
            "page_count",
        }

        assert all(key in result for key in required_keys)

    def test_document_id_generated(self, ingestion_service, simple_pdf):
        """Test that document ID is generated."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        doc_id = result["document_id"]
        assert doc_id is not None
        assert len(doc_id) > 0

    def test_filename_preserved(self, ingestion_service, simple_pdf):
        """Test that filename is preserved."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        assert result["filename"] == "simple.pdf"

    def test_metadata_generated(self, ingestion_service, simple_pdf):
        """Test that document metadata is generated."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        metadata = result["document_metadata"]
        assert metadata.document_id is not None
        assert metadata.filename is not None
        assert metadata.sha256 is not None
        assert metadata.page_count > 0
        assert metadata.chunk_count > 0

    def test_chunks_created(self, ingestion_service, simple_pdf):
        """Test that chunks are created."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        chunks = result["chunks"]
        assert len(chunks) > 0

        # Check first chunk has required fields
        chunk = chunks[0]
        assert chunk.chunk_id is not None
        assert chunk.document_id is not None
        assert chunk.text is not None
        assert len(chunk.text) > 0

    def test_chunk_count_matches(self, ingestion_service, simple_pdf):
        """Test that chunk count matches actual chunks."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        assert result["chunk_count"] == len(result["chunks"])

    def test_page_count_matches(self, ingestion_service, simple_pdf):
        """Test that page count is accurate."""
        result = ingestion_service.ingest_pdf(simple_pdf)

        # Simple PDF has 1 page
        assert result["page_count"] == 1

    def test_validate_document(self, ingestion_service, simple_pdf):
        """Test document validation without full ingestion."""
        result = ingestion_service.validate_document(simple_pdf)

        assert result["is_valid"] is True
        assert result["filename"] == "simple.pdf"
        assert result["page_count"] > 0
        assert result["has_extractable_text"] is True
        assert "file_hash" in result
        assert "file_size" in result

    def test_empty_pdf_raises_exception(self, ingestion_service, temp_dir):
        """Test that PDF with no extractable text raises exception."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter

            empty_pdf = temp_dir / "empty.pdf"
            c = canvas.Canvas(str(empty_pdf), pagesize=letter)
            # Draw nothing - empty page
            c.showPage()
            c.save()

            with pytest.raises(EmptyDocumentException):
                ingestion_service.ingest_pdf(empty_pdf)

        except ImportError:
            pytest.skip("reportlab not installed")

    def test_ingestion_twice_different_ids(self, ingestion_service, simple_pdf):
        """Test that ingesting same file twice generates different IDs."""
        result1 = ingestion_service.ingest_pdf(simple_pdf)
        result2 = ingestion_service.ingest_pdf(simple_pdf)

        # Document IDs should be different
        assert result1["document_id"] != result2["document_id"]

        # But file hashes should be the same
        assert result1["document_metadata"].sha256 == result2["document_metadata"].sha256
