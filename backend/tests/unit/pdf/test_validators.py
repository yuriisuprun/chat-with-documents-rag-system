"""
Unit tests for PDF validation.

Tests file size limits, PDF signature verification, and hash calculation.
"""

import hashlib
import tempfile
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.exceptions import FileSizeException, InvalidFileTypeException
from app.infrastructure.pdf.validators import (
    calculate_file_hash,
    validate_file_size,
    validate_pdf_file,
    validate_pdf_signature,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_pdf(temp_dir):
    """Create a minimal valid PDF file."""
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R>>endobj xref 0 4 0000000000 65535 f 0000000010 00000 n 0000000053 00000 n 0000000120 00000 n trailer<</Size 4/Root 1 0 R>>startxref 200 %%EOF"
    pdf_file = temp_dir / "test.pdf"
    pdf_file.write_bytes(pdf_content)
    return pdf_file


@pytest.fixture
def invalid_pdf(temp_dir):
    """Create a file with invalid PDF signature."""
    invalid_file = temp_dir / "invalid.pdf"
    invalid_file.write_bytes(b"This is not a PDF file")
    return invalid_file


class TestValidatePDFSignature:
    """Test PDF signature validation."""

    def test_valid_pdf_signature(self, valid_pdf):
        """Test that valid PDF signature is accepted."""
        assert validate_pdf_signature(valid_pdf) is True

    def test_invalid_pdf_signature(self, invalid_pdf):
        """Test that invalid PDF signature is rejected."""
        with pytest.raises(InvalidFileTypeException):
            validate_pdf_signature(invalid_pdf)

    def test_nonexistent_file(self, temp_dir):
        """Test that nonexistent file raises exception."""
        nonexistent = temp_dir / "nonexistent.pdf"
        with pytest.raises(InvalidFileTypeException):
            validate_pdf_signature(nonexistent)


class TestFileSize:
    """Test file size validation."""

    def test_valid_file_size(self, valid_pdf):
        """Test that appropriately sized file passes."""
        assert validate_file_size(valid_pdf) is True

    def test_oversized_file(self, temp_dir):
        """Test that oversized file is rejected."""
        large_file = temp_dir / "large.pdf"
        # Create file larger than max upload size
        with open(large_file, "wb") as f:
            f.write(b"x" * (settings.max_upload_size + 1))

        with pytest.raises(FileSizeException):
            validate_file_size(large_file)

    def test_file_size_exactly_at_limit(self, temp_dir):
        """Test that file exactly at limit passes."""
        limit_file = temp_dir / "at_limit.pdf"
        with open(limit_file, "wb") as f:
            f.write(b"x" * settings.max_upload_size)

        assert validate_file_size(limit_file) is True


class TestFileHash:
    """Test SHA-256 hash calculation."""

    def test_hash_calculation(self, temp_dir):
        """Test that hash is calculated correctly."""
        test_file = temp_dir / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)

        calculated_hash = calculate_file_hash(test_file)
        expected_hash = hashlib.sha256(content).hexdigest()

        assert calculated_hash == expected_hash

    def test_hash_consistency(self, valid_pdf):
        """Test that hash is consistent across calls."""
        hash1 = calculate_file_hash(valid_pdf)
        hash2 = calculate_file_hash(valid_pdf)

        assert hash1 == hash2

    def test_different_content_different_hash(self, temp_dir):
        """Test that different files produce different hashes."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2


class TestValidatePDFFile:
    """Test comprehensive PDF file validation."""

    def test_valid_pdf_validation(self, valid_pdf):
        """Test that valid PDF passes all checks."""
        result = validate_pdf_file(valid_pdf)

        assert result["is_valid"] is True
        assert result["filename"] == "test.pdf"
        assert result["file_size"] > 0
        assert len(result["file_hash"]) == 64  # SHA-256 is 64 hex chars

    def test_validation_includes_hash(self, valid_pdf):
        """Test that validation includes file hash."""
        result = validate_pdf_file(valid_pdf)
        expected_hash = calculate_file_hash(valid_pdf)

        assert result["file_hash"] == expected_hash

    def test_invalid_signature_rejected(self, invalid_pdf):
        """Test that invalid PDF signature is rejected."""
        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(invalid_pdf)

    def test_oversized_file_rejected(self, temp_dir):
        """Test that oversized PDF is rejected."""
        large_pdf = temp_dir / "large.pdf"
        with open(large_pdf, "wb") as f:
            # Write PDF signature + padding to exceed limit
            f.write(b"%PDF-1.4\n")
            f.write(b"x" * (settings.max_upload_size + 1))

        with pytest.raises(FileSizeException):
            validate_pdf_file(large_pdf)

    def test_nonexistent_file_rejected(self, temp_dir):
        """Test that nonexistent file is rejected."""
        nonexistent = temp_dir / "nonexistent.pdf"

        with pytest.raises(InvalidFileTypeException):
            validate_pdf_file(nonexistent)
