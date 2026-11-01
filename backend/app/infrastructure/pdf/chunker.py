"""
Text chunking with deterministic IDs and metadata preservation.

Uses RecursiveCharacterTextSplitter to chunk documents while preserving
document context and page numbers.
"""

import hashlib
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.exceptions import ChunkingException
from app.core.logging import get_logger
from app.infrastructure.pdf.models import Chunk, ChunkMetadata

logger = get_logger(__name__)


class PDFChunker:
    """Chunk extracted PDF text into overlapping segments."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """
        Initialize chunker with configuration.

        Args:
            chunk_size: Size of chunks in characters (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

        logger.debug(
            f"PDFChunker initialized: "
            f"chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )

    def chunk_page_text(
        self,
        text: str,
        page_number: int,
        document_id: str,
        filename: str,
    ) -> list[Chunk]:
        """
        Chunk text from a single PDF page.

        Args:
            text: Text content from page
            page_number: Page number (1-indexed)
            document_id: ID of document
            filename: Original filename

        Returns:
            List of Chunk objects

        Raises:
            ChunkingException: If chunking fails
        """
        if not text or not text.strip():
            return []

        try:
            chunks = self.splitter.split_text(text)
            result = []

            for chunk_index, chunk_text in enumerate(chunks):
                chunk_text = chunk_text.strip()

                # Skip empty chunks
                if not chunk_text:
                    continue

                # Generate deterministic chunk ID
                chunk_id = self._generate_chunk_id(
                    document_id, page_number, chunk_index
                )

                chunk = Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename=filename,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    text_length=len(chunk_text),
                )

                result.append(chunk)

            logger.debug(
                f"Chunked page {page_number} into {len(result)} chunks"
            )
            return result

        except Exception as e:
            raise ChunkingException(
                f"Failed to chunk page {page_number}: {str(e)}"
            )

    def chunk_extracted_pages(
        self,
        pages: list[dict],
        document_id: str,
        filename: str,
    ) -> list[Chunk]:
        """
        Chunk all extracted pages.

        Args:
            pages: List of page dicts from PDFExtractor
            document_id: ID of document
            filename: Original filename

        Returns:
            List of all Chunk objects

        Raises:
            ChunkingException: If chunking fails
        """
        all_chunks = []

        for page in pages:
            page_number = page["page_number"]
            text = page["text"]

            page_chunks = self.chunk_page_text(
                text, page_number, document_id, filename
            )
            all_chunks.extend(page_chunks)

        logger.info(
            f"Created {len(all_chunks)} chunks from {len(pages)} pages"
        )
        return all_chunks

    @staticmethod
    def _generate_chunk_id(
        document_id: str, page_number: int, chunk_index: int
    ) -> str:
        """
        Generate deterministic chunk ID.

        Based on document_id, page_number, and chunk_index to ensure
        same chunk always gets same ID.

        Args:
            document_id: Document UUID
            page_number: Page number
            chunk_index: Chunk index within page

        Returns:
            Hex-encoded chunk ID
        """
        identifier = f"{document_id}:page:{page_number}:chunk:{chunk_index}"
        chunk_id = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return chunk_id

    def get_metadata(self, chunk: Chunk) -> ChunkMetadata:
        """
        Extract metadata from chunk for storage.

        Args:
            chunk: Chunk object

        Returns:
            ChunkMetadata for this chunk
        """
        return ChunkMetadata(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
        )
