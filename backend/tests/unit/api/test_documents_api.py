"""
Unit tests for document management API endpoints.

Tests upload, list, get, and delete operations.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import (
    FileSizeException,
    InvalidFileTypeException,
    InvalidPDFException,
    PDFPageCountException,
    EmptyDocumentException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class TestDocumentUploadEndpoint:
    """Test document upload endpoint."""

    def test_upload_valid_pdf(self, app_with_mocked_documents):
        """Test uploading a valid PDF file."""
        client = app_with_mocked_documents
        
        file_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "test_doc_id"
        assert data["filename"] == "test.pdf"
        assert data["status"] == "indexed"

    def test_upload_invalid_file_type(self, app_with_mocked_documents):
        """Test uploading a non-PDF file."""
        client = app_with_mocked_documents
        
        # Mock the service to raise exception
        from app.api.dependencies import get_ingestion_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_ingestion_service]()
        mock_service.ingest_pdf.side_effect = InvalidFileTypeException("test.txt")

        file_content = b"This is not a PDF"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        )

        assert response.status_code == 400

    def test_upload_empty_file(self, app_with_mocked_documents):
        """Test uploading an empty file."""
        client = app_with_mocked_documents
        
        # Mock the service to raise exception
        from app.api.dependencies import get_ingestion_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_ingestion_service]()
        mock_service.ingest_pdf.side_effect = InvalidFileTypeException("empty.pdf")

        file_content = b""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    def test_upload_page_count_exceeded(self, app_with_mocked_documents):
        """Test uploading PDF with too many pages."""
        client = app_with_mocked_documents
        
        # Mock the service to raise exception
        from app.api.dependencies import get_ingestion_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_ingestion_service]()
        mock_service.ingest_pdf.side_effect = PDFPageCountException(150, 100)

        file_content = b"%PDF-1.4 large file"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    def test_upload_corrupted_pdf(self, app_with_mocked_documents):
        """Test uploading a corrupted PDF."""
        client = app_with_mocked_documents
        
        # Mock the service to raise exception
        from app.api.dependencies import get_ingestion_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_ingestion_service]()
        mock_service.ingest_pdf.side_effect = InvalidPDFException("corrupted.pdf", "corrupted file")

        file_content = b"%PDF-1.4 corrupted content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("corrupted.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    def test_upload_empty_document(self, app_with_mocked_documents):
        """Test uploading a PDF with no extractable text."""
        client = app_with_mocked_documents
        
        # Mock the service to raise exception
        from app.api.dependencies import get_ingestion_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_ingestion_service]()
        mock_service.ingest_pdf.side_effect = EmptyDocumentException("empty.pdf")

        file_content = b"%PDF-1.4 with no text"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 400

    def test_upload_indexing_failure(self, app_with_mocked_documents):
        """Test handling of indexing failure."""
        client = app_with_mocked_documents
        
        # Mock retrieval service to raise exception
        from app.api.dependencies import get_retrieval_service
        mock_service = app_with_mocked_documents.app.dependency_overrides[get_retrieval_service]()
        mock_service.index_document.side_effect = Exception("Indexing failed")

        file_content = b"%PDF-1.4 test content"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 500

    def test_upload_no_filename(self, app_with_mocked_documents):
        """Test uploading file with no filename."""
        client = app_with_mocked_documents
        
        file_content = b"%PDF-1.4 test"
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("", io.BytesIO(file_content), "application/pdf")},
        )

        # FastAPI validates filename at request level and returns 422
        assert response.status_code == 422


class TestDocumentListEndpoint:
    """Test document list endpoint."""

    def test_list_documents(self, app_with_mocked_retrieval):
        """Test listing documents."""
        client = app_with_mocked_retrieval
        
        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        # Response format depends on database/ChromaDB fallback
        assert isinstance(data, list)

    def test_list_empty_documents(self, app_with_mocked_retrieval):
        """Test listing when no documents indexed."""
        client = app_with_mocked_retrieval
        
        # Mock empty response
        from app.api.dependencies import get_retrieval_service
        mock_service = app_with_mocked_retrieval.app.dependency_overrides[get_retrieval_service]()
        mock_service.vector_store.collection.get.return_value = {"metadatas": []}

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_error_handling(self, app_with_mocked_retrieval):
        """Test error handling in list endpoint."""
        client = app_with_mocked_retrieval
        
        # Mock error
        from app.api.dependencies import get_retrieval_service
        mock_service = app_with_mocked_retrieval.app.dependency_overrides[get_retrieval_service]()
        mock_service.vector_store.collection.get.side_effect = Exception("Service error")

        response = client.get("/api/v1/documents")

        assert response.status_code == 200  # Returns empty list on fallback failure


class TestDocumentGetEndpoint:
    """Test document get endpoint."""

    def test_get_document_not_found(self, app_with_mocked_retrieval):
        """Test getting a document (Phase 7 feature)."""
        client = app_with_mocked_retrieval
        
        response = client.get("/api/v1/documents/doc_123")

        # Phase 7 returns 404 with message about database integration
        assert response.status_code == 404


class TestDocumentDeleteEndpoint:
    """Test document delete endpoint."""

    def test_delete_document(self, app_with_mocked_retrieval):
        """Test deleting a document."""
        client = app_with_mocked_retrieval
        
        response = client.delete("/api/v1/documents/doc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc_123"
        assert "20 chunks removed" in data["message"]

    def test_delete_nonexistent_document(self, app_with_mocked_retrieval):
        """Test deleting a non-existent document."""
        client = app_with_mocked_retrieval
        
        # Mock zero chunks deleted
        from app.api.dependencies import get_retrieval_service
        mock_service = app_with_mocked_retrieval.app.dependency_overrides[get_retrieval_service]()
        mock_service.delete_document_chunks.return_value = 0

        response = client.delete("/api/v1/documents/nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "nonexistent"

    def test_delete_error_handling(self, app_with_mocked_retrieval):
        """Test error handling in delete endpoint."""
        client = app_with_mocked_retrieval
        
        # Mock error
        from app.api.dependencies import get_retrieval_service
        mock_service = app_with_mocked_retrieval.app.dependency_overrides[get_retrieval_service]()
        mock_service.delete_document_chunks.side_effect = Exception("Delete failed")

        response = client.delete("/api/v1/documents/doc_123")

        assert response.status_code == 500

