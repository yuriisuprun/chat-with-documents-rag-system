"""
Unit tests for document management API endpoints.

Tests upload, list, get, and delete operations.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.documents import router
from app.core.exceptions import (
    FileSizeException,
    InvalidFileTypeException,
    InvalidPDFException,
    PDFPageCountException,
    EmptyDocumentException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_ingestion_service():
    """Create mock ingestion service."""
    service = MagicMock()
    service.ingest_pdf.return_value = {
        "document_id": "doc_123",
        "filename": "test_document.pdf",
        "chunks": [
            {
                "chunk_id": "chunk_1",
                "text": "This is a test chunk",
                "metadata": {
                    "document_id": "doc_123",
                    "page_number": 1,
                    "chunk_index": 0,
                },
            }
        ],
        "page_count": 5,
        "chunk_count": 10,
        "document_metadata": MagicMock(embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    }
    return service


@pytest.fixture
def mock_retrieval_service():
    """Create mock retrieval service."""
    service = MagicMock()
    service.index_document.return_value = 10
    service.get_collection_stats.return_value = {
        "chunk_count": 100,
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    }
    service.delete_document_chunks.return_value = 10
    return service


class TestDocumentUploadEndpoint:
    """Test document upload endpoint."""

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_valid_pdf(self, mock_get_ingestion, mock_get_retrieval, client):
        """Test uploading a valid PDF file."""
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

        file_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "doc_123"
        assert data["filename"] == "test.pdf"
        assert data["status"] == "indexed"

    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_invalid_file_type(self, mock_get_ingestion, client):
        """Test uploading a non-PDF file."""
        mock_ingestion = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_ingestion.ingest_pdf.side_effect = InvalidFileTypeException("test.txt")

        file_content = b"This is not a PDF"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        )

        assert response.status_code == 400

    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_empty_file(self, mock_get_ingestion, client):
        """Test uploading an empty file."""
        mock_ingestion = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_ingestion.ingest_pdf.side_effect = InvalidFileTypeException("empty.pdf")

        file_content = b""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_page_count_exceeded(self, mock_get_ingestion, client):
        """Test uploading PDF with too many pages."""
        mock_ingestion = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_ingestion.ingest_pdf.side_effect = PDFPageCountException(150, 100)

        file_content = b"%PDF-1.4 large file"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_corrupted_pdf(self, mock_get_ingestion, client):
        """Test uploading a corrupted PDF."""
        mock_ingestion = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_ingestion.ingest_pdf.side_effect = InvalidPDFException("corrupted.pdf", "corrupted file")

        file_content = b"%PDF-1.4 corrupted content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("corrupted.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_empty_document(self, mock_get_ingestion, client):
        """Test uploading a PDF with no extractable text."""
        mock_ingestion = MagicMock()
        mock_get_ingestion.return_value = mock_ingestion
        mock_ingestion.ingest_pdf.side_effect = EmptyDocumentException("empty.pdf")

        file_content = b"%PDF-1.4 with no text"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    @patch("app.api.routes.documents.get_retrieval_service")
    @patch("app.api.routes.documents.get_ingestion_service")
    def test_upload_indexing_failure(self, mock_get_ingestion, mock_get_retrieval, client):
        """Test handling of indexing failure."""
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
        mock_retrieval.index_document.side_effect = Exception("Indexing failed")

        file_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 500

    def test_upload_no_filename(self, client):
        """Test uploading file with no filename."""
        file_content = b"%PDF-1.4 test"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("", io.BytesIO(file_content), "application/pdf")},
        )

        # FastAPI validates filename at request level and returns 422
        assert response.status_code == 422


class TestDocumentListEndpoint:
    """Test document list endpoint."""

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_list_documents(self, mock_get_retrieval, client):
        """Test listing documents."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 100,
            "embedding_model": "test-model",
        }

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "count" in data
        assert data["count"] == 100

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_list_empty_documents(self, mock_get_retrieval, client):
        """Test listing when no documents indexed."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.get_collection_stats.return_value = {
            "chunk_count": 0,
            "embedding_model": "test-model",
        }

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["documents"]) == 0

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_list_error_handling(self, mock_get_retrieval, client):
        """Test error handling in list endpoint."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.get_collection_stats.side_effect = Exception("Service error")

        response = client.get("/api/v1/documents")

        assert response.status_code == 500


class TestDocumentGetEndpoint:
    """Test document get endpoint."""

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_get_document_not_found(self, mock_get_retrieval, client):
        """Test getting a document (Phase 7 feature)."""
        response = client.get("/api/v1/documents/doc_123")

        # Phase 7 returns 404 with message about database integration
        assert response.status_code == 404


class TestDocumentDeleteEndpoint:
    """Test document delete endpoint."""

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_delete_document(self, mock_get_retrieval, client):
        """Test deleting a document."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.delete_document_chunks.return_value = 10

        response = client.delete("/api/v1/documents/doc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc_123"
        assert "10 chunks removed" in data["message"]

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_delete_nonexistent_document(self, mock_get_retrieval, client):
        """Test deleting a non-existent document."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.delete_document_chunks.return_value = 0

        response = client.delete("/api/v1/documents/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "nonexistent"

    @patch("app.api.routes.documents.get_retrieval_service")
    def test_delete_error_handling(self, mock_get_retrieval, client):
        """Test error handling in delete endpoint."""
        mock_retrieval = MagicMock()
        mock_get_retrieval.return_value = mock_retrieval
        mock_retrieval.delete_document_chunks.side_effect = Exception("Delete failed")

        response = client.delete("/api/v1/documents/doc_123")

        assert response.status_code == 500
