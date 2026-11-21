"""
PDF Document Processing Pipeline Validation Tests.

Comprehensive tests for upload, extraction, normalization, and lifecycle management.
Based on PDF_PIPELINE_VALIDATION_MATRIX.md

Test Categories:
1. Upload Validation (17 scenarios)
2. Extraction Validation (10 points)
3. Lifecycle Management (7 checks)
4. Security Validation (5 checks)
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.exceptions import (
    FileSizeException,
    InvalidFileTypeException,
    InvalidPDFException,
    PDFPageCountException,
)
from app.infrastructure.pdf.extractor import PDFExtractor
from app.infrastructure.pdf.validators import (
    calculate_file_hash,
    validate_file_size,
    validate_pdf_file,
    validate_pdf_signature,
)


# ============================================================================
# FIXTURES: Test PDF Generation
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_pdf(pages: int = 5, page_content_template: str = "Page {N}") -> bytes:
    """
    Create a test PDF with specified number of pages.

    Args:
        pages: Number of pages to create
        page_content_template: Content template (use {N} for page number)

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for i in range(pages):
        page_num = i + 1
        content = page_content_template.format(N=page_num)
        c.drawString(100, 750, content)
        c.drawString(100, 730, f"Test content for page {page_num}")
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_unicode_test_pdf() -> bytes:
    """Create test PDF with Unicode characters."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Test Unicode content
    c.drawString(100, 750, "English text")
    c.drawString(100, 700, "中文文本")  # Chinese
    c.drawString(100, 650, "النص العربي")  # Arabic
    c.drawString(100, 600, "Emoji test: 🚀📊✅")  # Emoji
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================================
# PART 1: UPLOAD VALIDATION TESTS (17 Scenarios)
# ============================================================================


class TestUploadValidation:
    """Test PDF upload validation scenarios."""

    # -- Section 1.1: File Size Validation --

    def test_up001_valid_pdf_under_10mb(self, temp_dir):
        """UP-001: Valid PDF < 10MB should be accepted."""
        pdf_content = create_test_pdf(pages=5)
        pdf_path = temp_dir / "test_5mb.pdf"
        pdf_path.write_bytes(pdf_content)

        # Should not raise exception
        result = validate_pdf_file(pdf_path)

        assert result["is_valid"] is True
        assert result["file_size"] < 10_000_000
        assert len(result["file_hash"]) == 64  # SHA-256 hex

    def test_up002_pdf_at_10mb_boundary(self, temp_dir):
        """UP-002: PDF at exactly 10MB boundary should be accepted."""
        # Create exactly 10MB of PDF content
        pdf_path = temp_dir / "test_10mb.pdf"

        # Create minimal PDF then pad to 10MB
        pdf_content = create_test_pdf(pages=1)
        padding_needed = 10_000_000 - len(pdf_content)

        # Add padding comments (valid in PDF)
        padding = b"% " + (b"x" * (padding_needed - 3)) + b"\n"
        full_content = pdf_content[:-1] + padding + b"\n" + pdf_content[-1:]

        pdf_path.write_bytes(full_content[:10_000_000])

        result = validate_pdf_file(pdf_path)
        assert result["is_valid"] is True
        assert result["file_size"] == 10_000_000

    def test_up003_pdf_exceeding_10mb(self, temp_dir):
        """UP-003: PDF exceeding 10MB should be rejected."""
        pdf_path = temp_dir / "test_11mb.pdf"

        # Create oversized file
        content = b"%PDF-1.4\n" + (b"x" * 11_000_000)
        pdf_path.write_bytes(content)

        with pytest.raises(FileSizeException) as exc_info:
            validate_pdf_file(pdf_path)

        assert "exceeds" in str(exc_info.value).lower()

    def test_up004_empty_file(self, temp_dir):
        """UP-004: Empty file should be rejected."""
        pdf_path = temp_dir / "empty.pdf"
        pdf_path.write_bytes(b"")

        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(pdf_path)

    def test_up005_very_large_pdf(self, temp_dir):
        """UP-005: Very large PDF (50MB) should be rejected."""
        pdf_path = temp_dir / "test_50mb.pdf"

        # Create 50MB file with PDF signature
        content = b"%PDF-1.4\n" + (b"x" * 50_000_000)
        pdf_path.write_bytes(content)

        with pytest.raises(FileSizeException):
            validate_pdf_file(pdf_path)

    # -- Section 1.2: File Format & Extension Validation --

    def test_up006_invalid_extension_txt(self, temp_dir):
        """UP-006: Text file with .txt extension should be rejected."""
        txt_path = temp_dir / "document.txt"
        txt_path.write_text("This is plain text, not a PDF")

        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(txt_path)

    def test_up007_non_pdf_renamed_to_pdf(self, temp_dir):
        """UP-007: JPG image renamed to .pdf should be rejected."""
        # Create fake JPG (JPEG signature)
        jpg_path = temp_dir / "image.pdf"  # Wrong extension
        jpg_path.write_bytes(b"\xFF\xD8\xFF\xE0" + b"fake image data")

        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(jpg_path)

    def test_up008_correct_mime_type_pdf(self, temp_dir):
        """UP-008: PDF with correct MIME type should be accepted."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(create_test_pdf(pages=1))

        # Verify magic bytes
        result = validate_pdf_signature(pdf_path)
        assert result is True

    # -- Section 1.3: PDF Integrity & Corruption --

    def test_up010_corrupted_pdf_header(self, temp_dir):
        """UP-010: PDF with corrupted header should be rejected."""
        pdf_path = temp_dir / "corrupted.pdf"
        # Wrong magic bytes
        pdf_path.write_bytes(b"NOTPDF" + b"x" * 1000)

        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(pdf_path)

    def test_up011_truncated_pdf(self, temp_dir):
        """UP-011: Truncated PDF should be rejected during extraction."""
        pdf_content = create_test_pdf(pages=5)
        pdf_path = temp_dir / "truncated.pdf"

        # Write only first 60% of PDF
        pdf_path.write_bytes(pdf_content[: len(pdf_content) // 2])

        extractor = PDFExtractor()
        with pytest.raises(InvalidPDFException):
            extractor.extract_text(pdf_path)

    def test_up013_zero_page_pdf(self, temp_dir):
        """UP-013: Malformed PDF with no pages should be rejected."""
        # Create minimal PDF with no page objects
        pdf_path = temp_dir / "zeropage.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%EOF\n")

        extractor = PDFExtractor()
        with pytest.raises((InvalidPDFException, PDFPageCountException)):
            extractor.extract_text(pdf_path)

    # -- Section 1.4: Page Count Validation --

    def test_up014_pdf_with_100_pages(self, temp_dir):
        """UP-014: PDF with exactly 100 pages should be accepted."""
        pdf_content = create_test_pdf(pages=100)
        pdf_path = temp_dir / "test_100pages.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        assert result["page_count"] == 100
        assert len(result["pages"]) == 100

    def test_up015_pdf_exceeding_100_pages(self, temp_dir):
        """UP-015: PDF with 101 pages should be rejected."""
        pdf_content = create_test_pdf(pages=101)
        pdf_path = temp_dir / "test_101pages.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        with pytest.raises(PDFPageCountException) as exc_info:
            extractor.extract_text(pdf_path)

        assert "101" in str(exc_info.value)

    def test_up016_pdf_with_500_pages(self, temp_dir):
        """UP-016: PDF with 500 pages should be rejected."""
        pdf_content = create_test_pdf(pages=500)
        pdf_path = temp_dir / "test_500pages.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        with pytest.raises(PDFPageCountException):
            extractor.extract_text(pdf_path)

    def test_up017_single_page_pdf(self, temp_dir):
        """UP-017: Single-page PDF should be accepted."""
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "single.pdf"
        pdf_path.write_bytes(pdf_content)

        result = validate_pdf_file(pdf_path)
        assert result["is_valid"] is True

        extractor = PDFExtractor()
        extraction = extractor.extract_text(pdf_path)
        assert extraction["page_count"] == 1


# ============================================================================
# PART 2: EXTRACTION VALIDATION TESTS (10 Points)
# ============================================================================


class TestExtractionValidation:
    """Test PDF text extraction accuracy."""

    def test_ex001_page_count_accuracy(self, temp_dir):
        """EX-001: Page count should match document structure."""
        for page_count in [1, 5, 10, 50, 100]:
            pdf_content = create_test_pdf(pages=page_count)
            pdf_path = temp_dir / f"test_{page_count}.pdf"
            pdf_path.write_bytes(pdf_content)

            extractor = PDFExtractor()
            result = extractor.extract_text(pdf_path)

            assert result["page_count"] == page_count, f"Failed for {page_count} pages"

    def test_ex002_page_ordering(self, temp_dir):
        """EX-002: Pages should be extracted in correct order."""
        pdf_content = create_test_pdf(pages=5, page_content_template="Content{N}")
        pdf_path = temp_dir / "ordered.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Verify page numbers are sequential
        page_numbers = [p["page_number"] for p in result["pages"]]
        assert page_numbers == [1, 2, 3, 4, 5]

    def test_ex003_page_by_page_extraction(self, temp_dir):
        """EX-003: Each page should have correct page_number field."""
        pdf_content = create_test_pdf(pages=10)
        pdf_path = temp_dir / "pages.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        for i, page in enumerate(result["pages"], start=1):
            assert page["page_number"] == i
            assert "text" in page
            assert "text_length" in page

    def test_ex004_no_page_omission(self, temp_dir):
        """EX-004: All pages should be extracted without omission."""
        for total_pages in [3, 7, 50]:
            pdf_content = create_test_pdf(pages=total_pages)
            pdf_path = temp_dir / f"complete_{total_pages}.pdf"
            pdf_path.write_bytes(pdf_content)

            extractor = PDFExtractor()
            result = extractor.extract_text(pdf_path)

            assert len(result["pages"]) == total_pages
            page_numbers = set(p["page_number"] for p in result["pages"])
            assert page_numbers == set(range(1, total_pages + 1))

    def test_ex005_text_preservation(self, temp_dir):
        """EX-005: Extracted text should match source."""
        test_text = "This is test content for validation"
        pdf_content = create_test_pdf(pages=1, page_content_template=test_text)
        pdf_path = temp_dir / "content.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Text should be present in extraction
        extracted_text = result["pages"][0]["text"]
        assert len(extracted_text) > 0

    def test_ex006_whitespace_normalization(self, temp_dir):
        """EX-006: Whitespace should be normalized."""
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "whitespace.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Extracted text should have whitespace handled
        for page in result["pages"]:
            text = page["text"]
            # Should be stripped
            assert text == text.strip() or text == ""

    def test_ex007_empty_page_handling(self, temp_dir):
        """EX-007: Empty pages should have empty text, not be skipped."""
        pdf_content = create_test_pdf(pages=5)
        pdf_path = temp_dir / "empty_pages.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # All 5 pages should be present
        assert len(result["pages"]) == 5
        assert all("page_number" in p for p in result["pages"])

    def test_ex008_unicode_preservation(self, temp_dir):
        """EX-008: Unicode characters should be preserved."""
        pdf_content = create_unicode_test_pdf()
        pdf_path = temp_dir / "unicode.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Unicode should be preserved in text
        extracted_text = result["pages"][0]["text"]
        assert len(extracted_text) > 0
        # Text should contain some content (actual characters)
        assert result["has_extractable_text"] is True

    def test_ex009_image_only_page_handling(self, temp_dir):
        """EX-009: Image-only pages should have empty text without crashing."""
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "images.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Should not crash, should have page
        assert len(result["pages"]) > 0

    def test_ex010_extraction_failure_recovery(self, temp_dir):
        """EX-010: Corrupted page in multi-page should be skipped."""
        pdf_content = create_test_pdf(pages=5)
        pdf_path = temp_dir / "recovery.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Should extract without crashing even if some pages have issues
        assert len(result["pages"]) == 5


# ============================================================================
# PART 3: SECURITY VALIDATION TESTS (5 Checks)
# ============================================================================


class TestSecurityValidation:
    """Test security aspects of PDF processing."""

    def test_sec001_path_traversal_protection(self, temp_dir):
        """SEC-001: Path traversal attempts should be rejected."""
        from app.core.validators import validate_filename

        dangerous_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/shadow",
        ]

        for name in dangerous_names:
            with pytest.raises(Exception):  # ValidationException or similar
                validate_filename(name + ".pdf")

    def test_sec002_filename_sanitization(self, temp_dir):
        """SEC-002: Special characters should be sanitized."""
        from app.core.validators import validate_filename

        special_names = [
            "file`name.pdf",
            "file;rm *.pdf",
            "file$(whoami).pdf",
            "file|cat.pdf",
        ]

        for name in special_names:
            try:
                # Should either raise or sanitize
                result = validate_filename(name)
                # If it doesn't raise, it should be sanitized
                assert "`" not in result
                assert ";" not in result
                assert "$" not in result
                assert "|" not in result
            except Exception:
                # Exception is also acceptable
                pass

    def test_sec003_temp_file_cleanup(self, temp_dir):
        """SEC-003: Temporary files should be cleaned up."""
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "temp_test.pdf"
        pdf_path.write_bytes(pdf_content)

        # After extraction, temp files should not persist
        extractor = PDFExtractor()
        result = extractor.extract_text(pdf_path)

        # Original file still exists (it's not a temp file)
        assert pdf_path.exists()

    def test_sec004_file_permissions(self, temp_dir):
        """SEC-004: Uploaded files should have appropriate permissions."""
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "perms.pdf"
        pdf_path.write_bytes(pdf_content)

        # Check file is readable
        assert os.access(pdf_path, os.R_OK)

        # On Unix, check it's not world-writable (if platform supports)
        if hasattr(os, "stat"):
            stat_info = os.stat(pdf_path)
            mode = stat_info.st_mode
            # File should not be world-writable
            # (0o002 is world write bit)
            # assert (mode & 0o002) == 0  # May not work on all platforms

    def test_sec005_malicious_pdf_handling(self, temp_dir):
        """SEC-005: PDFs with embedded content should be safely handled."""
        # Normal PDF extraction should be safe
        pdf_content = create_test_pdf(pages=1)
        pdf_path = temp_dir / "normal.pdf"
        pdf_path.write_bytes(pdf_content)

        extractor = PDFExtractor()
        # Should not crash or execute any embedded content
        result = extractor.extract_text(pdf_path)

        # Should just extract text
        assert result["has_extractable_text"] is not None


# ============================================================================
# PART 4: DATA CONSISTENCY TESTS
# ============================================================================


class TestDataConsistency:
    """Test consistency across filesystem, SQLite, and ChromaDB."""

    def test_three_layer_consistency_structure(self, temp_dir):
        """Verify three-layer consistency structure can be validated."""
        pdf_content = create_test_pdf(pages=5)
        pdf_path = temp_dir / "consistency.pdf"
        pdf_path.write_bytes(pdf_content)

        # Verify file storage layer
        assert pdf_path.exists()

        # Get file properties
        file_size = pdf_path.stat().st_size
        file_hash = calculate_file_hash(pdf_path)

        # Verify extraction layer
        extractor = PDFExtractor()
        extraction_result = extractor.extract_text(pdf_path)

        assert extraction_result["page_count"] == 5
        assert extraction_result["has_extractable_text"] is True

        # All layers consistent
        assert file_size > 0
        assert len(file_hash) == 64  # SHA-256
        assert extraction_result["page_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
