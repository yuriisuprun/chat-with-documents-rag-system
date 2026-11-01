"""
RAG (Retrieval-Augmented Generation) service.

Orchestrates retrieval, context assembly, and LLM generation.
"""

from typing import Optional

from app.core.config import settings
from app.core.exceptions import LLMUnavailableException, RAGException
from app.core.logging import get_logger
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.vectorstore.base import RetrievedChunk
from app.prompts.rag_prompt import build_rag_prompt, build_sufficiency_check_prompt
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)


class RAGService:
    """Service for retrieval-augmented generation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_provider: Optional[OllamaProvider] = None,
    ):
        """
        Initialize RAG service.

        Args:
            retrieval_service: Retrieval service (creates new if not provided)
            llm_provider: LLM provider (creates Ollama if not provided)
        """
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_provider = llm_provider or OllamaProvider()

        logger.debug(
            f"RAGService initialized: llm_model={self.llm_provider.get_model_name()}"
        )

    def answer_question(
        self,
        question: str,
        document_ids: Optional[list[str]] = None,
        top_k: int = 4,
    ) -> dict:
        """
        Answer a question using RAG pipeline.

        Steps:
        1. Retrieve relevant chunks
        2. Assemble context
        3. Check context sufficiency
        4. Generate answer with LLM
        5. Extract and format sources

        Args:
            question: User question
            document_ids: Optional list of document IDs to search
            top_k: Number of chunks to retrieve

        Returns:
            Dictionary with:
            - query: Original question
            - answer: Generated answer
            - sources: List of source references
            - context_sufficient: Whether context was adequate
            - retrieval_count: Number of chunks retrieved

        Raises:
            RAGException: If any step fails
        """
        try:
            logger.info(f"Answering question: '{question[:50]}...'")

            # Step 1: Retrieve relevant chunks
            logger.debug("Step 1: Retrieving relevant chunks")
            try:
                retrieved_chunks = self.retrieval_service.retrieve(
                    query=question,
                    top_k=top_k,
                    document_ids=document_ids,
                )
                retrieval_count = len(retrieved_chunks)
                logger.debug(f"Retrieved {retrieval_count} chunks")
            except Exception as e:
                logger.error(f"Retrieval failed: {e}")
                raise RAGException(f"Failed to retrieve context: {str(e)}")

            # Step 2: Assemble context
            logger.debug("Step 2: Assembling context")
            context = self._assemble_context(retrieved_chunks)
            context_length = len(context)
            logger.debug(f"Context assembled: {context_length} characters")

            # Step 3: Check context sufficiency (optional)
            logger.debug("Step 3: Checking context sufficiency")
            context_sufficient = True
            if settings.rag_check_sufficiency and context:
                try:
                    context_sufficient = self._check_sufficiency(question, context)
                    logger.debug(f"Context sufficiency: {context_sufficient}")
                except Exception as e:
                    logger.warning(f"Sufficiency check failed: {e}, proceeding anyway")
                    context_sufficient = False

            # Step 4: Generate answer
            logger.debug("Step 4: Generating answer with LLM")
            try:
                prompt = build_rag_prompt(question, context)
                answer = self.llm_provider.generate(prompt)
                logger.debug(f"Answer generated: {len(answer)} characters")
            except LLMUnavailableException as e:
                logger.error(f"LLM generation failed: {e}")
                raise RAGException(f"Failed to generate answer: {str(e)}")

            # Step 5: Extract sources
            logger.debug("Step 5: Extracting source references")
            sources = self._extract_sources(retrieved_chunks)
            logger.debug(f"Extracted {len(sources)} sources")

            result = {
                "query": question,
                "answer": answer,
                "sources": sources,
                "context_sufficient": context_sufficient,
                "retrieval_count": retrieval_count,
            }

            logger.info(f"Question answered successfully with {len(sources)} sources")
            return result

        except RAGException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in RAG pipeline: {e}")
            raise RAGException(f"RAG pipeline failed: {str(e)}")

    def _assemble_context(self, chunks: list[RetrievedChunk]) -> str:
        """
        Assemble context from retrieved chunks.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        # Sort by page number for readability
        sorted_chunks = sorted(chunks, key=lambda x: (
            x.metadata.get("page_number", 0),
            x.metadata.get("chunk_index", 0),
        ))

        context_parts = []
        for chunk in sorted_chunks:
            page = chunk.metadata.get("page_number", "?")
            context_parts.append(f"[Page {page}]\n{chunk.text}")

        context = "\n\n".join(context_parts)

        # Truncate if too long
        if len(context) > settings.rag_max_context_tokens * 4:  # Rough token estimate
            logger.warning("Context exceeds max size, truncating")
            context = context[: settings.rag_max_context_tokens * 4]

        return context

    def _check_sufficiency(self, question: str, context: str) -> bool:
        """
        Check if context is sufficient to answer question.

        Uses LLM to validate.

        Args:
            question: User question
            context: Retrieved context

        Returns:
            True if context is sufficient
        """
        try:
            prompt = build_sufficiency_check_prompt(question, context)
            response = self.llm_provider.generate(prompt, temperature=0.0)

            # Check response
            response_upper = response.upper().strip()
            if "SUFFICIENT" in response_upper:
                return True
            return False

        except Exception as e:
            logger.warning(f"Sufficiency check error: {e}")
            return False

    @staticmethod
    def _extract_sources(chunks: list[RetrievedChunk]) -> list[dict]:
        """
        Extract and deduplicate source references from chunks.

        Args:
            chunks: Retrieved chunks with metadata

        Returns:
            List of unique source references
        """
        sources = []
        seen_sources = set()

        for chunk in chunks:
            # Build source reference from metadata
            source_key = (
                chunk.metadata.get("document_id"),
                chunk.metadata.get("page_number"),
                chunk.metadata.get("filename"),
            )

            # Skip duplicates
            if source_key in seen_sources:
                continue

            seen_sources.add(source_key)

            source = {
                "filename": chunk.metadata.get("filename", "Unknown"),
                "page_number": chunk.metadata.get("page_number", 0),
                "document_id": chunk.metadata.get("document_id", "Unknown"),
            }
            sources.append(source)

        # Sort by page number
        sources.sort(key=lambda x: x.get("page_number", 0))

        return sources
