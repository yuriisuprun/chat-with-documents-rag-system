"""
Unit tests for text chunking.

Tests chunk generation, deterministic IDs, and metadata preservation.
"""

import uuid

import pytest

from app.infrastructure.pdf.chunker import PDFChunker
from app.infrastructure.pdf.models import Chunk, ChunkMetadata


@pytest.fixture
def chunker():
    """Create PDF chunker instance."""
    return PDFChunker(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def sample_text():
    """Create sample text for chunking."""
    return """
    This is a sample document with multiple paragraphs.

    This is the second paragraph with some additional content
    to make it longer. It contains multiple sentences.

    This is the third paragraph. It demonstrates how the chunker
    will break text into smaller pieces while preserving structure.
    """


class TestChunking:
    """Test text chunking functionality."""

    def test_chunk_page_text_returns_chunks(self, chunker, sample_text):
        """Test that chunking returns list of chunks."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_chunks_have_required_fields(self, chunker, sample_text):
        """Test that chunks have all required fields."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        required_fields = {
            "chunk_id",
            "document_id",
            "filename",
            "page_number",
            "chunk_index",
            "text",
            "text_length",
        }

        for chunk in chunks:
            assert hasattr(chunk, "chunk_id")
            assert hasattr(chunk, "document_id")
            assert hasattr(chunk, "filename")
            assert hasattr(chunk, "page_number")
            assert hasattr(chunk, "chunk_index")
            assert hasattr(chunk, "text")
            assert hasattr(chunk, "text_length")

    def test_chunk_text_not_empty(self, chunker, sample_text):
        """Test that chunks contain non-empty text."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        for chunk in chunks:
            assert len(chunk.text) > 0
            assert chunk.text.strip() == chunk.text

    def test_chunk_text_length_accurate(self, chunker, sample_text):
        """Test that text_length matches actual text length."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        for chunk in chunks:
            assert chunk.text_length == len(chunk.text)

    def test_page_number_preserved(self, chunker, sample_text):
        """Test that page numbers are preserved."""
        doc_id = str(uuid.uuid4())

        chunks_page_1 = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")
        chunks_page_2 = chunker.chunk_page_text(sample_text, 2, doc_id, "test.pdf")

        for chunk in chunks_page_1:
            assert chunk.page_number == 1

        for chunk in chunks_page_2:
            assert chunk.page_number == 2

    def test_document_id_preserved(self, chunker, sample_text):
        """Test that document ID is preserved in chunks."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        for chunk in chunks:
            assert chunk.document_id == doc_id

    def test_filename_preserved(self, chunker, sample_text):
        """Test that filename is preserved in chunks."""
        doc_id = str(uuid.uuid4())
        filename = "my_document.pdf"
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, filename)

        for chunk in chunks:
            assert chunk.filename == filename

    def test_empty_text_returns_empty_list(self, chunker):
        """Test that empty text produces no chunks."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text("", 1, doc_id, "test.pdf")

        assert len(chunks) == 0

    def test_whitespace_only_text_returns_empty_list(self, chunker):
        """Test that whitespace-only text produces no chunks."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text("   \n\n   ", 1, doc_id, "test.pdf")

        assert len(chunks) == 0


class TestDeterministicChunkIDs:
    """Test deterministic chunk ID generation."""

    def test_chunk_id_deterministic(self, chunker, sample_text):
        """Test that same input produces same chunk IDs."""
        doc_id = str(uuid.uuid4())

        chunks_1 = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")
        chunks_2 = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        assert len(chunks_1) == len(chunks_2)

        for c1, c2 in zip(chunks_1, chunks_2):
            assert c1.chunk_id == c2.chunk_id

    def test_different_pages_different_ids(self, chunker, sample_text):
        """Test that same text on different pages has different IDs."""
        doc_id = str(uuid.uuid4())

        chunks_page_1 = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")
        chunks_page_2 = chunker.chunk_page_text(sample_text, 2, doc_id, "test.pdf")

        # First chunk ID should be different
        assert chunks_page_1[0].chunk_id != chunks_page_2[0].chunk_id

    def test_different_documents_different_ids(self, chunker, sample_text):
        """Test that same text in different documents has different IDs."""
        doc_id_1 = str(uuid.uuid4())
        doc_id_2 = str(uuid.uuid4())

        chunks_doc_1 = chunker.chunk_page_text(sample_text, 1, doc_id_1, "test.pdf")
        chunks_doc_2 = chunker.chunk_page_text(sample_text, 1, doc_id_2, "test.pdf")

        # IDs should be different
        assert chunks_doc_1[0].chunk_id != chunks_doc_2[0].chunk_id

    def test_chunk_id_format(self, chunker, sample_text):
        """Test that chunk IDs are hex strings of expected length."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        for chunk in chunks:
            # Should be 16-char hex string
            assert len(chunk.chunk_id) == 16
            int(chunk.chunk_id, 16)  # Should be valid hex


class TestChunkMetadata:
    """Test metadata extraction from chunks."""

    def test_get_metadata_from_chunk(self, chunker, sample_text):
        """Test that metadata can be extracted from chunk."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        chunk = chunks[0]
        metadata = chunker.get_metadata(chunk)

        assert isinstance(metadata, ChunkMetadata)
        assert metadata.chunk_id == chunk.chunk_id
        assert metadata.document_id == chunk.document_id
        assert metadata.filename == chunk.filename
        assert metadata.page_number == chunk.page_number
        assert metadata.chunk_index == chunk.chunk_index

    def test_metadata_to_dict(self, chunker, sample_text):
        """Test that metadata can be converted to dict."""
        doc_id = str(uuid.uuid4())
        chunks = chunker.chunk_page_text(sample_text, 1, doc_id, "test.pdf")

        chunk = chunks[0]
        metadata = chunker.get_metadata(chunk)
        metadata_dict = metadata.to_dict()

        assert isinstance(metadata_dict, dict)
        assert "chunk_id" in metadata_dict
        assert "document_id" in metadata_dict
        assert "filename" in metadata_dict
        assert "page_number" in metadata_dict
        assert "chunk_index" in metadata_dict


class TestChunkExtractedPages:
    """Test chunking of extracted pages."""

    def test_chunk_multiple_pages(self, chunker, sample_text):
        """Test chunking multiple extracted pages."""
        doc_id = str(uuid.uuid4())

        pages = [
            {"page_number": 1, "text": sample_text},
            {"page_number": 2, "text": sample_text},
        ]

        chunks = chunker.chunk_extracted_pages(pages, doc_id, "test.pdf")

        assert len(chunks) > 0
        # Should have chunks from both pages
        page_numbers = {chunk.page_number for chunk in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_empty_pages_skipped(self, chunker):
        """Test that empty pages are skipped."""
        doc_id = str(uuid.uuid4())

        pages = [
            {"page_number": 1, "text": ""},
            {"page_number": 2, "text": "Some text content here"},
        ]

        chunks = chunker.chunk_extracted_pages(pages, doc_id, "test.pdf")

        # Should only have chunks from page 2
        page_numbers = {chunk.page_number for chunk in chunks}
        assert 1 not in page_numbers
        assert 2 in page_numbers
