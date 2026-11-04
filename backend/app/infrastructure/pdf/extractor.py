"""
PDF text extraction using PyMuPDF.

Extracts text page-by-page, preserving structure and page numbers.
"""

from pathlib import Path

from app.core.config import settings
from app.core.exceptions import InvalidPDFException, PDFPageCountException
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extract text from PDF documents."""

    def extract_text(self, file_path: Path) -> dict:
        """
        Extract text from PDF file.

        Validates page count and extracts text page-by-page, preserving
        page numbers for later reference in chunks.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary containing:
            - pages: List of dicts with 'page_number' and 'text'
            - page_count: Total number of pages
            - has_extractable_text: Whether any text was extracted

        Raises:
            InvalidPDFException: If PDF is corrupted or unreadable
            PDFPageCountException: If page count exceeds limit
        """
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz

            # Open PDF
            doc = fitz.open(file_path)

            # Validate page count
            page_count = doc.page_count
            if page_count > settings.max_pdf_pages:
                doc.close()
                raise PDFPageCountException(page_count, settings.max_pdf_pages)

            logger.debug(f"Extracting text from {file_path.name} ({page_count} pages)")

            # Extract text page by page
            pages = []
            total_text_length = 0

            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    text = page.get_text()

                    # Clean up extracted text
                    text = text.strip()

                    pages.append({
                        "page_number": page_num + 1,  # 1-indexed for display
                        "text": text,
                        "text_length": len(text),
                    })

                    total_text_length += len(text)

                except Exception as e:
                    logger.warning(
                        f"Error extracting page {page_num + 1} from {file_path.name}: {e}"
                    )
                    # Continue with next page
                    pages.append({
                        "page_number": page_num + 1,
                        "text": "",
                        "text_length": 0,
                    })

            doc.close()

            has_extractable_text = total_text_length > 0

            logger.debug(
                f"Extracted {total_text_length} characters from {file_path.name}"
            )

            return {
                "pages": pages,
                "page_count": page_count,
                "has_extractable_text": has_extractable_text,
                "total_text_length": total_text_length,
            }

        except PDFPageCountException:
            # Re-raise page count exceptions
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path.name}: {e}")
            raise InvalidPDFException(file_path.name, str(e))

    def get_page_count(self, file_path: Path) -> int:
        """
        Get page count without extracting text.

        Args:
            file_path: Path to PDF file

        Returns:
            Number of pages

        Raises:
            InvalidPDFException: If PDF cannot be opened
        """
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz

            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
        except Exception as e:
            raise InvalidPDFException(file_path.name, f"Cannot read page count: {str(e)}")

    def validate_extractable_text(self, file_path: Path) -> bool:
        """
        Check if PDF has extractable text.

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF has extractable text

        Raises:
            InvalidPDFException: If PDF cannot be opened
        """
        try:
            result = self.extract_text(file_path)
            return result["has_extractable_text"]
        except PDFPageCountException:
            raise
        except Exception as e:
            raise InvalidPDFException(
                file_path.name, f"Cannot validate extractable text: {str(e)}"
            )
