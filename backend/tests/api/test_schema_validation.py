"""
Response schema validation tests for Chat With Documents API.

Validates that actual API responses match defined Pydantic schemas:
- All required fields present
- Fields have correct types
- Status codes consistent
- Error responses properly formatted
- Frontend expectations met

Total: 20+ schema validation tests
"""

import io
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.api.dependencies import (
    get_rag_service,
    get_ingestion_service,
    get_retrieval_service,
)
from app.schemas.chat import (
    ChatResponse,
    HealthCheckResponse,
    SourceReference,
    ErrorResponse,
)
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentDeleteResponse,
)


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
# HealthCheckResponse Schema Tests
# ============================================================================

class TestHealthCheckResponseSchema:
    """Validate HealthCheckResponse schema."""

    def test_health_response_valid_schema(self, client_with_mocks):
        """Test health response matches HealthCheckResponse schema."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        # Should not raise ValidationError
        health_response = HealthCheckResponse(**data)
        assert health_response.status is not None
        assert health_response.services is not None

    def test_health_status_enum_values(self, client_with_mocks):
        """Test health status has valid values."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert data["status"] in valid_statuses

    def test_health_services_is_dict(self, client_with_mocks):
        """Test health services is a dict."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["services"], dict)
        for key, value in data["services"].items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_health_version_is_string(self, client_with_mocks):
        """Test health version is a string."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_timestamp_is_string(self, client_with_mocks):
        """Test health timestamp is a string."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        assert isinstance(data["timestamp"], str)
        # Should be ISO format or similar
        assert "T" in data["timestamp"] or len(data["timestamp"]) > 10


# ============================================================================
# DocumentUploadResponse Schema Tests
# ============================================================================

class TestDocumentUploadResponseSchema:
    """Validate DocumentUploadResponse schema."""

    def test_upload_response_valid_schema(self, client_with_mocks, test_pdf_file):
        """Test upload response matches DocumentUploadResponse schema."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        # Should not raise ValidationError
        upload_response = DocumentUploadResponse(**data)
        assert upload_response.document_id is not None
        assert upload_response.filename is not None

    def test_upload_document_id_not_empty(self, client_with_mocks, test_pdf_file):
        """Test upload response document_id is not empty."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        assert data["document_id"]
        assert len(data["document_id"]) > 0
        assert isinstance(data["document_id"], str)

    def test_upload_filename_matches_input(self, client_with_mocks, test_pdf_file):
        """Test upload response filename matches or sanitizes input."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("my_document.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        # Filename should contain the original or sanitized version
        assert "document" in data["filename"].lower() or "my_document" in data["filename"]

    def test_upload_status_valid_value(self, client_with_mocks, test_pdf_file):
        """Test upload response status has valid value."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        valid_statuses = ["pending", "processing", "indexed", "failed"]
        assert data["status"] in valid_statuses

    def test_upload_message_not_empty(self, client_with_mocks, test_pdf_file):
        """Test upload response message is not empty."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        assert data["message"]
        assert len(data["message"]) > 0
        assert isinstance(data["message"], str)

    def test_upload_all_required_fields_present(self, client_with_mocks, test_pdf_file):
        """Test upload response has all required fields."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        data = response.json()
        required_fields = {"document_id", "filename", "status", "message"}
        assert required_fields.issubset(data.keys())


# ============================================================================
# ChatResponse Schema Tests
# ============================================================================

class TestChatResponseSchema:
    """Validate ChatResponse schema."""

    def test_chat_response_valid_schema(self, client_with_mocks):
        """Test chat response matches ChatResponse schema."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        # Should not raise ValidationError
        chat_response = ChatResponse(**data)
        assert chat_response.query is not None
        assert chat_response.answer is not None
        assert chat_response.sources is not None

    def test_chat_query_matches_request(self, client_with_mocks):
        """Test chat response query matches request."""
        query = "What is the document about?"
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": query},
        )
        
        data = response.json()
        assert data["query"] == query

    def test_chat_answer_is_string(self, client_with_mocks):
        """Test chat response answer is a string."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_chat_sources_is_list(self, client_with_mocks):
        """Test chat response sources is a list."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        assert isinstance(data["sources"], list)

    def test_chat_context_sufficient_is_bool(self, client_with_mocks):
        """Test chat response context_sufficient is boolean."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        assert isinstance(data["context_sufficient"], bool)

    def test_chat_source_schema_valid(self, client_with_mocks):
        """Test chat response sources have valid schema."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?", "include_sources": True},
        )
        
        data = response.json()
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            # Should match SourceReference schema
            source_ref = SourceReference(**source)
            assert source_ref.document_id is not None
            assert source_ref.filename is not None

    def test_chat_source_fields_correct_types(self, client_with_mocks):
        """Test chat source fields have correct types."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?", "include_sources": True},
        )
        
        data = response.json()
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert isinstance(source["document_id"], str)
            assert isinstance(source["filename"], str)
            assert isinstance(source["page_number"], int)
            assert isinstance(source["chunk_index"], int)
            assert isinstance(source["similarity_score"], (int, float))
            assert isinstance(source["text_preview"], str)

    def test_chat_similarity_score_in_range(self, client_with_mocks):
        """Test chat source similarity scores are in valid range."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?", "include_sources": True},
        )
        
        data = response.json()
        for source in data["sources"]:
            score = source["similarity_score"]
            assert 0 <= score <= 1.0, f"Similarity score {score} out of range"

    def test_chat_all_required_fields_present(self, client_with_mocks):
        """Test chat response has all required fields."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        data = response.json()
        required_fields = {"query", "answer", "sources", "context_sufficient"}
        assert required_fields.issubset(data.keys())


# ============================================================================
# DocumentDeleteResponse Schema Tests
# ============================================================================

class TestDocumentDeleteResponseSchema:
    """Validate DocumentDeleteResponse schema."""

    def test_delete_response_valid_schema(self, client_with_mocks):
        """Test delete response matches DocumentDeleteResponse schema."""
        response = client_with_mocks.delete("/api/v1/documents/test_doc")
        
        data = response.json()
        # Should not raise ValidationError
        delete_response = DocumentDeleteResponse(**data)
        assert delete_response.document_id is not None

    def test_delete_response_has_message(self, client_with_mocks):
        """Test delete response contains message."""
        response = client_with_mocks.delete("/api/v1/documents/test_doc")
        
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_delete_response_document_id_matches(self, client_with_mocks):
        """Test delete response document_id matches request."""
        doc_id = "test_doc_123"
        response = client_with_mocks.delete(f"/api/v1/documents/{doc_id}")
        
        data = response.json()
        assert data["document_id"] == doc_id


# ============================================================================
# Error Response Schema Tests
# ============================================================================

class TestErrorResponseSchema:
    """Validate error response schemas."""

    def test_invalid_query_error_schema(self, client_with_mocks):
        """Test error response for invalid query."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": ""},  # Empty query
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        # Should have error details
        assert "detail" in data or "error" in data

    def test_missing_required_field_error(self, client_with_mocks):
        """Test error response for missing required field."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={},  # Missing query
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_invalid_json_error(self, client_with_mocks):
        """Test error response for invalid JSON."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_type_validation_error(self, client_with_mocks):
        """Test error response for type validation."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": 123},  # Should be string
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data


# ============================================================================
# Response Format Consistency Tests
# ============================================================================

class TestResponseFormatConsistency:
    """Test response format consistency across endpoints."""

    def test_all_json_responses_have_consistent_structure(self, client_with_mocks):
        """Test all endpoints return valid JSON."""
        endpoints = [
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/readyz"),
            ("GET", "/api/v1/documents"),
            ("GET", "/api/v1/chat/history"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = client_with_mocks.get(path)
            
            # Should be valid JSON
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert data is not None

    def test_error_responses_consistent_format(self, client_with_mocks):
        """Test error responses have consistent format."""
        # Trigger multiple errors
        error_responses = [
            client_with_mocks.post("/api/v1/chat", json={}),  # Missing field
            client_with_mocks.get("/api/v1/invalid"),  # Not found
        ]
        
        for response in error_responses:
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert isinstance(data, dict)

    def test_successful_responses_include_data(self, client_with_mocks):
        """Test successful responses include meaningful data."""
        response = client_with_mocks.get("/api/v1/health")
        data = response.json()
        
        # Should have actual data, not just status
        assert len(data) > 0
        assert data is not None

    def test_response_codes_match_status(self, client_with_mocks):
        """Test HTTP status codes are appropriate."""
        success_responses = [
            ("GET", "/api/v1/health", status.HTTP_200_OK),
            ("GET", "/api/v1/readyz", status.HTTP_200_OK),
            ("GET", "/api/v1/documents", status.HTTP_200_OK),
        ]
        
        for method, path, expected_status in success_responses:
            if method == "GET":
                response = client_with_mocks.get(path)
            
            assert response.status_code == expected_status
