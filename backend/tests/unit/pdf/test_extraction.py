"""
Unit tests for PDF text extraction.

Tests page extraction, page count validation, and empty document handling.
"""

import tempfile
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.exceptions import InvalidPDFException, PDFPageCountException
from app.infrastructure.pdf.extractor import PDFExtractor


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def extractor():
    """Create PDF extractor instance."""
    return PDFExtractor()


@pytest.fixture
def simple_pdf(temp_dir):
    """Create a simple PDF with text content using reportlab."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_path = temp_dir / "simple.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Page 1
        c.drawString(100, 750, "This is page 1")
        c.drawString(100, 730, "Line 2 on page 1")
        c.showPage()

        # Page 2
        c.drawString(100, 750, "This is page 2")
        c.drawString(100, 730, "Line 2 on page 2")
        c.showPage()

        c.save()
        return pdf_path
    except ImportError:
        pytest.skip("reportlab not installed")


@pytest.fixture
def invalid_pdf(temp_dir):
    """Create invalid PDF file."""
    invalid_pdf_path = temp_dir / "invalid.pdf"
    invalid_pdf_path.write_bytes(b"not a real pdf")
    return invalid_pdf_path


class TestPDFExtraction:
    """Test PDF text extraction."""

    def test_extract_text_returns_pages(self, extractor, simple_pdf):
        """Test that extraction returns page list."""
        result = extractor.extract_text(simple_pdf)

        assert "pages" in result
        assert "page_count" in result
        assert "has_extractable_text" in result
        assert isinstance(result["pages"], list)

    def test_page_count_accuracy(self, extractor, simple_pdf):
        """Test that page count is accurate."""
        result = extractor.extract_text(simple_pdf)

        assert result["page_count"] == 2

    def test_pages_have_correct_numbers(self, extractor, simple_pdf):
        """Test that page numbers are 1-indexed and correct."""
        result = extractor.extract_text(simple_pdf)
        pages = result["pages"]

        assert pages[0]["page_number"] == 1
        assert pages[1]["page_number"] == 2

    def test_pages_have_text(self, extractor, simple_pdf):
        """Test that extracted pages contain text."""
        result = extractor.extract_text(simple_pdf)
        pages = result["pages"]

        # At least one page should have text
        has_text = any(page["text_length"] > 0 for page in pages)
        assert has_text

    def test_has_extractable_text_true_for_text_pdf(self, extractor, simple_pdf):
        """Test that PDFs with text report as extractable."""
        result = extractor.extract_text(simple_pdf)

        assert result["has_extractable_text"] is True

    def test_text_length_tracked(self, extractor, simple_pdf):
        """Test that text length is tracked for each page."""
        result = extractor.extract_text(simple_pdf)
        pages = result["pages"]

        assert all("text_length" in page for page in pages)
        assert all(isinstance(page["text_length"], int) for page in pages)

    def test_total_text_length(self, extractor, simple_pdf):
        """Test that total text length is calculated."""
        result = extractor.extract_text(simple_pdf)

        assert "total_text_length" in result
        assert result["total_text_length"] > 0

    def test_invalid_pdf_raises_exception(self, extractor, invalid_pdf):
        """Test that invalid PDF raises exception."""
        with pytest.raises(InvalidPDFException):
            extractor.extract_text(invalid_pdf)

    def test_get_page_count(self, extractor, simple_pdf):
        """Test page count can be retrieved without extraction."""
        page_count = extractor.get_page_count(simple_pdf)

        assert page_count == 2

    def test_validate_extractable_text(self, extractor, simple_pdf):
        """Test validation of extractable text."""
        has_text = extractor.validate_extractable_text(simple_pdf)

        assert has_text is True

    def test_page_count_exceeds_limit(self, extractor, temp_dir):
        """Test that PDF with too many pages raises exception."""
        # This test would require creating a PDF with many pages
        # For now, we'll mock the settings
        pytest.skip("Requires multi-page PDF generation")


class TestPDFExtractionEdgeCases:
    """Test edge cases in PDF extraction."""

    def test_empty_pages_handled(self, extractor, temp_dir):
        """Test that empty pages are handled correctly."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter

            pdf_path = temp_dir / "empty_pages.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)

            # Empty page
            c.showPage()

            # Page with text
            c.drawString(100, 750, "Some text")
            c.showPage()

            c.save()

            result = extractor.extract_text(pdf_path)
            pages = result["pages"]

            # Should have 2 pages
            assert len(pages) == 2
            # First page might be empty
            assert pages[0]["text_length"] == 0
            # Second page should have text
            assert pages[1]["text_length"] > 0

        except ImportError:
            pytest.skip("reportlab not installed")
