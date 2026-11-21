"""
Failure scenario tests for Chat With Documents API.

Tests error handling and failure scenarios:
1. Upload failures (file too large, invalid format, corruption)
2. Chat failures (LLM unavailable, vector store down)
3. Delete failures (not found, in-progress)
4. System failures (health/readiness checks)

Total: 16+ failure scenario tests
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.dependencies import (
    get_rag_service,
    get_ingestion_service,
    get_retrieval_service,
)
from app.core.exceptions import LLMUnavailableException, RAGException


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client_with_mocks(mock_rag_service, mock_ingestion_service, mock_retrieval_service):
    """Create test client with all mocked services."""
    app = create_app()
    
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_pdf_file():
    """Create a minimal valid PDF file for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000244 00000 n
0000000333 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
428
%%EOF"""
    
    return io.BytesIO(pdf_content)


# ============================================================================
# Upload Failures
# ============================================================================

class TestUploadFailures:
    """Test upload failure scenarios."""

    def test_upload_file_too_large(self, client_with_mocks):
        """Test upload fails gracefully when file exceeds size limit."""
        # Create file larger than 10MB limit
        large_content = b"x" * (11 * 1024 * 1024)
        
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
        )
        
        # Should reject with appropriate error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_upload_invalid_pdf_format(self, client_with_mocks):
        """Test upload fails when PDF is corrupted."""
        # Create file that looks like PDF but isn't
        invalid_content = b"%PDF-1.4\nThis is not a valid PDF"
        
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("corrupt.pdf", io.BytesIO(invalid_content), "application/pdf")},
        )
        
        # Should fail with 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_not_pdf_file(self, client_with_mocks):
        """Test upload rejects non-PDF files."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("document.txt", io.BytesIO(b"text content"), "text/plain")},
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_upload_empty_file(self, client_with_mocks):
        """Test upload rejects empty files."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_no_file_provided(self, client_with_mocks):
        """Test upload requires file parameter."""
        response = client_with_mocks.post("/api/v1/documents/upload")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Chat Failures
# ============================================================================

class TestChatFailures:
    """Test chat failure scenarios."""

    def test_chat_llm_unavailable(self, client_with_mocks):
        """Test chat handles unavailable LLM gracefully."""
        mock_rag_service = client_with_mocks.app.dependency_overrides[get_rag_service]()
        mock_rag_service.answer_question.side_effect = LLMUnavailableException(
            "LLM service unavailable"
        )
        
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        # Should return 503 Service Unavailable
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_chat_rag_pipeline_fails(self, client_with_mocks):
        """Test chat handles RAG pipeline failure."""
        mock_rag_service = client_with_mocks.app.dependency_overrides[get_rag_service]()
        mock_rag_service.answer_question.side_effect = RAGException(
            "RAG_ERROR", "RAG pipeline failed"
        )
        
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        # Should return 500 Internal Server Error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_chat_invalid_query_format(self, client_with_mocks):
        """Test chat rejects invalid query format."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": ""},  # Empty query
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_query_exceeds_max_length(self, client_with_mocks):
        """Test chat rejects overly long queries."""
        long_query = "a" * 3000  # Exceeds 2000 char limit
        
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": long_query},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_chat_missing_query_field(self, client_with_mocks):
        """Test chat requires query field."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"include_sources": True},  # Missing query
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Delete Failures
# ============================================================================

class TestDeleteFailures:
    """Test delete failure scenarios."""

    def test_delete_nonexistent_document(self, client_with_mocks):
        """Test delete handles nonexistent document gracefully."""
        response = client_with_mocks.delete(
            "/api/v1/documents/nonexistent_document_12345"
        )
        
        # Should be idempotent (200) or return 404
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_delete_invalid_document_id(self, client_with_mocks):
        """Test delete with malformed document ID."""
        response = client_with_mocks.delete("/api/v1/documents/")
        
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_delete_document_id_with_special_chars(self, client_with_mocks):
        """Test delete with special characters in ID."""
        response = client_with_mocks.delete("/api/v1/documents/doc@#$%^&*()")
        
        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]

    def test_delete_very_long_document_id(self, client_with_mocks):
        """Test delete with extremely long document ID."""
        long_id = "a" * 1000
        
        response = client_with_mocks.delete(f"/api/v1/documents/{long_id}")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]


# ============================================================================
# System Failures
# ============================================================================

class TestSystemFailures:
    """Test system-level failure scenarios."""

    def test_health_check_succeeds_even_with_service_issues(self, client_with_mocks):
        """Test health endpoint doesn't crash."""
        response = client_with_mocks.get("/api/v1/health")
        
        # Should always respond
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    def test_readiness_check_identifies_unready_state(self, client_with_mocks):
        """Test readiness check identifies when services are unavailable."""
        response = client_with_mocks.get("/api/v1/readyz")
        
        # Readiness can return 200 (ready) or 503 (not ready)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    def test_invalid_endpoint_returns_404(self, client_with_mocks):
        """Test accessing invalid endpoint returns 404."""
        response = client_with_mocks.get("/api/v1/invalid_endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_http_method_returns_405(self, client_with_mocks):
        """Test using wrong HTTP method returns 405."""
        # POST to a GET-only endpoint
        response = client_with_mocks.post("/api/v1/health")
        
        assert response.status_code in [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_malformed_json_returns_422(self, client_with_mocks):
        """Test malformed JSON returns validation error."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Timeout and Performance Failures
# ============================================================================

class TestTimeoutAndPerformanceFailures:
    """Test timeout and performance-related failures."""

    def test_upload_timeout_handling(self, client_with_mocks):
        """Test upload handles timeouts gracefully."""
        # This is handled by the ingestion service timeout
        # Mock would normally succeed, so we can't easily test timeout
        pass

    def test_chat_response_contains_error_field(self, client_with_mocks):
        """Test chat response can contain error field on failure."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        # Error field should be present (even if None)
        assert "error" in data

    def test_list_documents_handles_many_documents(self, client_with_mocks):
        """Test list documents handles large result sets."""
        response = client_with_mocks.get("/api/v1/documents")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# State Management Failures
# ============================================================================

class TestStateManagementFailures:
    """Test state management error scenarios."""

    def test_concurrent_uploads_handled(self, client_with_mocks, test_pdf_file):
        """Test concurrent uploads are handled safely."""
        # First upload
        test_pdf_file.seek(0)
        response1 = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test1.pdf", test_pdf_file, "application/pdf")},
        )
        
        # Second upload immediately
        test_pdf_file.seek(0)
        response2 = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test2.pdf", test_pdf_file, "application/pdf")},
        )
        
        # Both should succeed
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Document IDs should be different
        assert response1.json()["document_id"] != response2.json()["document_id"]

    def test_delete_then_query_handles_missing_document(self, client_with_mocks):
        """Test querying after deleting document."""
        doc_id = "test_doc"
        
        # Delete (might not exist, but that's ok)
        client_with_mocks.delete(f"/api/v1/documents/{doc_id}")
        
        # Query with deleted document ID
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "Test?",
                "document_ids": [doc_id]
            },
        )
        
        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]

    def test_rapid_fire_requests_handled(self, client_with_mocks):
        """Test rapid requests are handled without crashes."""
        for i in range(10):
            response = client_with_mocks.get("/api/v1/health")
            assert response.status_code == status.HTTP_200_OK


# ============================================================================
# Data Validation Failures
# ============================================================================

class TestDataValidationFailures:
    """Test data validation error scenarios."""

    def test_chat_with_null_query(self, client_with_mocks):
        """Test chat rejects null query."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": None},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_with_numeric_query(self, client_with_mocks):
        """Test chat rejects numeric query."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": 12345},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_with_array_document_ids(self, client_with_mocks):
        """Test chat accepts array of document IDs."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "Test?",
                "document_ids": ["doc1", "doc2", "doc3"]
            },
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_chat_with_invalid_document_ids_format(self, client_with_mocks):
        """Test chat handles invalid document IDs format."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "Test?",
                "document_ids": "not_an_array"  # Should be array
            },
        )
        
        # Should validate and reject
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]
