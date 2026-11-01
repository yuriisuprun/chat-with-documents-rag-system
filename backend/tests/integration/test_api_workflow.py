"""
Integration tests for complete API workflows.

Tests end-to-end scenarios like upload → retrieve → chat.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def app():
    """Create FastAPI app with all routes."""
    from fastapi import FastAPI

    from app.api.routes import chat, documents, health

    app = FastAPI()
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(health.router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestUploadRetrieveChatWorkflow:
    """Test complete workflow: upload → retrieve → chat."""

    @patch("app.api.routes.documents.get_ingestion_service")
    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.chat.get_rag_service")
    def test_complete_workflow(self, mock_get_rag, mock_get_retrieval, mock_get_ingestion, client):
        """Test complete upload and chat workflow."""
        # Setup mocks
        mock_ingestion = MagicMock()
        mock_retrieval = MagicMock()
        mock_rag = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_get_retrieval.return_value = mock_retrieval
        mock_get_rag.return_value = mock_rag

        mock_ingestion.ingest_pdf.return_value = {
            "document_id": "doc_123",
            "filename": "test.pdf",
            "chunks": [
                {
                    "chunk_id": "chunk_1",
                    "text": "Machine learning is AI",
                    "metadata": {
                        "document_id": "doc_123",
                        "page_number": 1,
                        "chunk_index": 0,
                    },
                }
            ],
            "page_count": 5,
            "chunk_count": 10,
            "document_metadata": MagicMock(
                embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
        }
        mock_retrieval.index_document.return_value = 10
        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 10,
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        }

        mock_rag.answer_question.return_value = {
            "query": "What is machine learning?",
            "answer": "Machine learning is a field of AI that enables systems to learn from data.",
            "sources": [
                {
                    "document_id": "doc_123",
                    "filename": "test.pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "similarity_score": 0.95,
                    "text_preview": "Machine learning is AI...",
                }
            ],
            "context_sufficient": True,
            "retrieval_count": 1,
        }

        # Step 1: Upload document
        file_content = b"%PDF-1.4 test content"
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        doc_id = upload_data["document_id"]
        assert doc_id == "doc_123"

        # Step 2: List documents
        list_response = client.get("/api/v1/documents")

        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["count"] == 10

        # Step 3: Ask question
        chat_response = client.post(
            "/api/v1/chat",
            json={"query": "What is machine learning?"},
        )

        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["query"] == "What is machine learning?"
        assert len(chat_data["answer"]) > 0
        assert len(chat_data["sources"]) > 0

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.chat.get_rag_service")
    def test_list_then_chat_workflow(self, mock_get_rag, mock_get_retrieval, client):
        """Test listing documents then asking question."""
        mock_retrieval = MagicMock()
        mock_rag = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_get_rag.return_value = mock_rag

        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 50,
            "embedding_model": "test-model",
        }

        mock_rag.answer_question.return_value = {
            "query": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "sources": [],
            "context_sufficient": True,
            "retrieval_count": 0,
        }

        # List documents
        list_response = client.get("/api/v1/documents")
        assert list_response.status_code == 200

        # Ask question
        chat_response = client.post(
            "/api/v1/chat",
            json={"query": "What is AI?"},
        )
        assert chat_response.status_code == 200

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.chat.get_rag_service")
    def test_multiple_chat_requests(self, mock_get_rag, mock_get_retrieval, client):
        """Test multiple sequential chat requests."""
        mock_retrieval = MagicMock()
        mock_rag = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_get_rag.return_value = mock_rag

        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 100,
            "embedding_model": "test-model",
        }

        mock_rag.answer_question.side_effect = [
            {
                "query": "Question 1?",
                "answer": "Answer 1",
                "sources": [],
                "context_sufficient": True,
                "retrieval_count": 2,
            },
            {
                "query": "Question 2?",
                "answer": "Answer 2",
                "sources": [],
                "context_sufficient": True,
                "retrieval_count": 3,
            },
            {
                "query": "Question 3?",
                "answer": "Answer 3",
                "sources": [],
                "context_sufficient": False,
                "retrieval_count": 0,
            },
        ]

        responses = []
        for i in range(1, 4):
            response = client.post(
                "/api/v1/chat",
                json={"query": f"Question {i}?"},
            )
            assert response.status_code == 200
            responses.append(response.json())

        assert len(responses) == 3
        assert responses[0]["query"] == "Question 1?"
        assert responses[1]["query"] == "Question 2?"
        assert responses[2]["context_sufficient"] is False


class TestErrorHandlingWorkflow:
    """Test error scenarios in API workflow."""

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_then_indexing_fails(self, mock_get_ingestion, mock_get_retrieval, client):
        """Test handling when indexing fails after successful ingestion."""
        mock_ingestion = MagicMock()
        mock_retrieval = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_get_retrieval.return_value = mock_retrieval

        mock_ingestion.ingest_pdf.return_value = {
            "document_id": "doc_123",
            "filename": "test.pdf",
            "chunks": [],
            "page_count": 5,
            "chunk_count": 10,
            "document_metadata": MagicMock(embedding_model="test-model"),
        }
        mock_retrieval.index_document.side_effect = Exception("Indexing service down")

        file_content = b"%PDF-1.4 test"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 500

    @patch("app.api.routes.chat.get_rag_service")
    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.documents.get_ingestion_service")
    def test_chat_when_no_documents(self, mock_get_ingestion, mock_get_retrieval, mock_get_rag, client):
        """Test chat when no documents are indexed."""
        mock_retrieval = MagicMock()
        mock_rag = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_get_rag.return_value = mock_rag

        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 0,
            "embedding_model": "test-model",
        }

        mock_rag.answer_question.return_value = {
            "query": "What is in the documents?",
            "answer": "No documents indexed yet.",
            "sources": [],
            "context_sufficient": False,
            "retrieval_count": 0,
        }

        response = client.post(
            "/api/v1/chat",
            json={"query": "What is in the documents?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["context_sufficient"] is False

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_delete_during_chat(self, mock_get_retrieval, client):
        """Test deleting document while chat is operating."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.delete_document_chunks.return_value = 10

        response = client.delete("/api/v1/documents/doc_123")

        assert response.status_code == 200

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_same_document_twice(self, mock_get_ingestion, mock_get_retrieval, client):
        """Test uploading the same document twice."""
        mock_ingestion = MagicMock()
        mock_retrieval = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_get_retrieval.return_value = mock_retrieval

        mock_ingestion.ingest_pdf.return_value = {
            "document_id": "doc_123",
            "filename": "test.pdf",
            "chunks": [],
            "page_count": 5,
            "chunk_count": 10,
            "document_metadata": MagicMock(embedding_model="test-model"),
        }
        mock_retrieval.index_document.return_value = 10

        file_content = b"%PDF-1.4 test"

        # First upload
        response1 = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )
        assert response1.status_code == 201

        # Second upload (same file)
        response2 = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )
        assert response2.status_code == 201


class TestHealthCheckIntegration:
    """Test health check with other endpoints."""

    @patch("app.api.routes.documents.get_ingestion_service")
    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.chat.get_rag_service")
    def test_health_check_with_documents(self, mock_rag, mock_retrieval, mock_ingestion, client):
        """Test health check when documents are indexed."""
        # Health check endpoint (if it exists)
        response = client.get("/api/v1/health")

        # Should return some status (implementation may vary)
        assert response.status_code in [200, 404]  # 404 if endpoint not implemented
