"""RAG (Retrieval-Augmented Generation) service for knowledge base."""

import logging
from typing import Optional, List
from app.config import settings
from app.models import DocumentChunk, KnowledgeDocument
from app.services.language_service import LanguageService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation."""

    CHUNK_SIZE = 500  # Characters per chunk
    CHUNK_OVERLAP = 100  # Overlap between chunks
    TOP_K = 3  # Number of chunks to retrieve

    def __init__(self):
        """Initialize RAG service."""
        self.chunk_size = self.CHUNK_SIZE
        self.chunk_overlap = self.CHUNK_OVERLAP
        self.top_k = self.TOP_K
        self.language_service = LanguageService()

    def chunk_text(self, text: str, chunk_size: Optional[int] = None, detect_language: bool = True) -> List[dict]:
        """
        Split text into overlapping chunks with language detection.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            detect_language: Whether to detect language for each chunk
            
        Returns:
            List of dicts with 'content' and 'language' keys
        """
        chunk_size = chunk_size or self.chunk_size
        chunks = []
        
        for i in range(0, len(text), chunk_size - self.chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                # Detect language for each chunk if requested
                detected_lang = None
                if detect_language:
                    detected_lang, _ = self.language_service.detect_language(chunk)
                
                chunks.append({
                    "content": chunk,
                    "language": detected_lang or settings.TENANT_DEFAULT_LANGUAGE
                })
        
        return chunks

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        return ai_service.generate_embedding(text)

    def retrieve_context(
        self,
        query: str,
        db: Session,
        language: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Optional[str]:
        """
        Retrieve relevant context from knowledge base using vector search with language awareness.
        
        Args:
            query: Query text
            db: Database session
            language: ISO 639-1 language code to prioritize results
            top_k: Number of chunks to retrieve
            
        Returns:
            Concatenated relevant context or None
        """
        try:
            from pgvector.sqlalchemy import func as pgvector_func
            
            top_k = top_k or self.top_k
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return None

            # Build base query
            query_builder = db.query(
                DocumentChunk.content,
                DocumentChunk.detected_language,
                pgvector_func.l2_distance(
                    DocumentChunk.embedding,
                    query_embedding
                ).label("distance")
            ).join(
                KnowledgeDocument
            ).filter(
                KnowledgeDocument.is_active == True,
                DocumentChunk.embedding != None,
            )
            
            # Prioritize language-matched results if language specified
            if language and self.language_service.is_language_supported(language):
                # Get same language results first
                same_lang_results = query_builder.filter(
                    DocumentChunk.detected_language == language
                ).order_by("distance").limit(top_k).all()
                
                if same_lang_results:
                    # If we got enough results in same language, use those
                    results = same_lang_results
                else:
                    # Otherwise fall back to any language
                    results = query_builder.order_by("distance").limit(top_k).all()
            else:
                # No language specified, get best results regardless of language
                results = query_builder.order_by("distance").limit(top_k).all()

            if not results:
                logger.info(f"No relevant context found")
                return None

            # Concatenate results
            context_parts = [f"- {chunk[0]}" for chunk in results]
            context = "\n".join(context_parts)
            
            logger.debug(f"Retrieved {len(results)} context chunks in language(s): {[r[1] for r in results]}")
            return context if context.strip() else None

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return None

    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            return text if text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None

    def extract_text_from_docx(self, file_path: str) -> Optional[str]:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text or None
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text if text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return None

    def extract_text_from_txt(self, file_path: str) -> Optional[str]:
        """
        Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text or None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            return text if text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            return None

    def extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """
        Extract text from any supported file type.
        
        Args:
            file_path: Path to file
            file_type: File type (pdf, docx, txt)
            
        Returns:
            Extracted text or None
        """
        extractors = {
            "pdf": self.extract_text_from_pdf,
            "docx": self.extract_text_from_docx,
            "txt": self.extract_text_from_txt,
        }

        extractor = extractors.get(file_type.lower())
        if not extractor:
            logger.error(f"Unsupported file type: {file_type}")
            return None

        return extractor(file_path)
