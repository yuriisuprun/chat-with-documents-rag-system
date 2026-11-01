"""
Unit tests for RAG service.

Tests answer generation, context assembly, and source extraction.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.vectorstore.base import RetrievedChunk
from app.services.rag_service import RAGService


@pytest.fixture
def mock_retrieval_service():
    """Create mock retrieval service."""
    service = MagicMock()
    service.retrieve.return_value = [
        RetrievedChunk(
            chunk_id="chunk_1",
            text="Machine learning is a field of AI",
            similarity_score=0.92,
            metadata={
                "document_id": "doc_1",
                "filename": "ai_book.pdf",
                "page_number": 5,
            },
        ),
        RetrievedChunk(
            chunk_id="chunk_2",
            text="Neural networks process information",
            similarity_score=0.85,
            metadata={
                "document_id": "doc_1",
                "filename": "ai_book.pdf",
                "page_number": 8,
            },
        ),
    ]
    return service


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    provider = MagicMock()
    provider.generate.return_value = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
    provider.get_model_name.return_value = "test-model"
    return provider


@pytest.fixture
def rag_service(mock_retrieval_service, mock_llm_provider):
    """Create RAG service with mocked dependencies."""
    return RAGService(
        retrieval_service=mock_retrieval_service,
        llm_provider=mock_llm_provider,
    )


class TestRAGService:
    """Test RAG service operations."""

    def test_answer_question_returns_dict(self, rag_service):
        """Test that answer_question returns structured result."""
        result = rag_service.answer_question("What is machine learning?")

        assert isinstance(result, dict)
        assert "query" in result
        assert "answer" in result
        assert "sources" in result
        assert "context_sufficient" in result
        assert "retrieval_count" in result

    def test_answer_question_includes_answer(self, rag_service):
        """Test that answer is included in result."""
        result = rag_service.answer_question("What is machine learning?")

        assert result["answer"] is not None
        assert len(result["answer"]) > 0

    def test_answer_question_includes_sources(self, rag_service):
        """Test that sources are included."""
        result = rag_service.answer_question("What is machine learning?")

        assert len(result["sources"]) > 0
        assert all("filename" in s for s in result["sources"])
        assert all("page_number" in s for s in result["sources"])

    def test_answer_question_retrieval_called(self, rag_service, mock_retrieval_service):
        """Test that retrieval is called."""
        rag_service.answer_question("What is AI?", top_k=5)

        mock_retrieval_service.retrieve.assert_called_once()
        call_args = mock_retrieval_service.retrieve.call_args
        assert call_args[1]["top_k"] == 5

    def test_answer_question_llm_called(self, rag_service, mock_llm_provider):
        """Test that LLM is called."""
        rag_service.answer_question("What is AI?")

        mock_llm_provider.generate.assert_called_once()
        # Check that prompt was passed
        call_args = mock_llm_provider.generate.call_args
        assert "What is AI?" in call_args[0][0]

    def test_answer_question_with_document_filter(self, rag_service, mock_retrieval_service):
        """Test that document filter is passed to retrieval."""
        doc_ids = ["doc_1", "doc_2"]

        rag_service.answer_question("Question?", document_ids=doc_ids)

        call_args = mock_retrieval_service.retrieve.call_args
        assert call_args[1]["document_ids"] == doc_ids

    def test_retrieval_count_accurate(self, rag_service):
        """Test that retrieval count matches returned chunks."""
        result = rag_service.answer_question("What is AI?")

        assert result["retrieval_count"] == len(result["sources"])

    def test_answer_question_preserves_query(self, rag_service):
        """Test that original query is preserved."""
        query = "What is artificial intelligence?"

        result = rag_service.answer_question(query)

        assert result["query"] == query

    def test_sources_deduplicated(self, rag_service, mock_retrieval_service):
        """Test that duplicate sources are removed."""
        # Add duplicate chunks with same page
        mock_retrieval_service.retrieve.return_value = [
            RetrievedChunk(
                chunk_id="chunk_1",
                text="Text 1",
                similarity_score=0.9,
                metadata={
                    "document_id": "doc_1",
                    "filename": "doc.pdf",
                    "page_number": 5,
                },
            ),
            RetrievedChunk(
                chunk_id="chunk_2",
                text="Text 2",
                similarity_score=0.85,
                metadata={
                    "document_id": "doc_1",
                    "filename": "doc.pdf",
                    "page_number": 5,  # Same page
                },
            ),
        ]

        result = rag_service.answer_question("Question?")

        # Should only have one source (deduplicated)
        assert len(result["sources"]) == 1

    def test_sources_sorted_by_page(self, rag_service, mock_retrieval_service):
        """Test that sources are sorted by page number."""
        mock_retrieval_service.retrieve.return_value = [
            RetrievedChunk(
                chunk_id="chunk_1",
                text="Text",
                similarity_score=0.9,
                metadata={"document_id": "doc_1", "filename": "doc.pdf", "page_number": 10},
            ),
            RetrievedChunk(
                chunk_id="chunk_2",
                text="Text",
                similarity_score=0.85,
                metadata={"document_id": "doc_1", "filename": "doc.pdf", "page_number": 5},
            ),
        ]

        result = rag_service.answer_question("Question?")

        # Should be sorted by page number
        assert result["sources"][0]["page_number"] == 5
        assert result["sources"][1]["page_number"] == 10


class TestRAGServiceContextAssembly:
    """Test context assembly in RAG service."""

    def test_assemble_context_includes_all_chunks(self, rag_service):
        """Test that all chunks are included in context."""
        chunks = [
            RetrievedChunk(
                chunk_id="chunk_1",
                text="First text",
                similarity_score=0.9,
                metadata={"page_number": 1},
            ),
            RetrievedChunk(
                chunk_id="chunk_2",
                text="Second text",
                similarity_score=0.85,
                metadata={"page_number": 2},
            ),
        ]

        context = rag_service._assemble_context(chunks)

        assert "First text" in context
        assert "Second text" in context

    def test_assemble_context_includes_page_numbers(self, rag_service):
        """Test that page numbers are included in context."""
        chunks = [
            RetrievedChunk(
                chunk_id="chunk_1",
                text="Content",
                similarity_score=0.9,
                metadata={"page_number": 5},
            ),
        ]

        context = rag_service._assemble_context(chunks)

        assert "[Page 5]" in context

    def test_assemble_context_empty_chunks(self, rag_service):
        """Test context assembly with empty chunk list."""
        context = rag_service._assemble_context([])

        assert context == ""


class TestRAGServiceSufficiency:
    """Test context sufficiency checking."""

    def test_sufficiency_check_success(self, rag_service, mock_llm_provider):
        """Test successful sufficiency check."""
        mock_llm_provider.generate.return_value = "SUFFICIENT"

        result = rag_service._check_sufficiency("Question?", "Context text")

        assert result is True

    def test_sufficiency_check_insufficient(self, rag_service, mock_llm_provider):
        """Test insufficient context detection."""
        mock_llm_provider.generate.return_value = "INSUFFICIENT"

        result = rag_service._check_sufficiency("Question?", "Context text")

        assert result is False

    def test_sufficiency_check_error_handling(self, rag_service, mock_llm_provider):
        """Test error handling in sufficiency check."""
        mock_llm_provider.generate.side_effect = Exception("LLM error")

        result = rag_service._check_sufficiency("Question?", "Context")

        # Should return False on error rather than raise
        assert result is False
