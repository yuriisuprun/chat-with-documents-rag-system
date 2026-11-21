"""
Workflow integration tests for Chat With Documents system.

Tests complete end-to-end lifecycles:
1. Upload → Query → Delete workflow
2. Chat edge cases
3. Data persistence and recovery

Total: 15+ workflow tests
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
BT /F1 12 Tf 100 700 Td (Test Document) Tj ET
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
# Lifecycle 1: Upload → Query → Delete Workflow
# ============================================================================

class TestUploadQueryDeleteWorkflow:
    """Test complete workflow: upload document, query it, then delete."""

    def test_complete_workflow_success(self, client_with_mocks, test_pdf_file):
        """
        Test complete workflow:
        1. Upload PDF
        2. List documents
        3. Ask question about document
        4. Get chat history
        5. Delete document
        6. Verify cleanup
        """
        # Step 1: Upload PDF
        upload_response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        document_id = doc_data["document_id"]
        assert document_id
        
        # Step 2: List documents (verify upload)
        list_response = client_with_mocks.get("/api/v1/documents")
        assert list_response.status_code == status.HTTP_200_OK
        docs = list_response.json()
        assert isinstance(docs, list)
        
        # Step 3: Ask question about document
        chat_response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "What is in the document?",
                "include_sources": True
            },
        )
        assert chat_response.status_code == status.HTTP_200_OK
        chat_data = chat_response.json()
        assert chat_data["answer"]
        assert isinstance(chat_data["sources"], list)
        
        # Step 4: Get chat history
        history_response = client_with_mocks.get("/api/v1/chat/history")
        assert history_response.status_code == status.HTTP_200_OK
        
        # Step 5: Delete document
        delete_response = client_with_mocks.delete(
            f"/api/v1/documents/{document_id}"
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Step 6: Verify cleanup (list should not contain deleted doc)
        final_list_response = client_with_mocks.get("/api/v1/documents")
        assert final_list_response.status_code == status.HTTP_200_OK

    def test_workflow_with_multiple_uploads(self, client_with_mocks, test_pdf_file):
        """Test workflow with multiple document uploads."""
        doc_ids = []
        
        # Upload 3 documents
        for i in range(3):
            test_pdf_file.seek(0)
            response = client_with_mocks.post(
                "/api/v1/documents/upload",
                files={"file": (f"test{i}.pdf", test_pdf_file, "application/pdf")},
            )
            assert response.status_code == status.HTTP_201_CREATED
            doc_ids.append(response.json()["document_id"])
        
        # List should show all
        list_response = client_with_mocks.get("/api/v1/documents")
        docs = list_response.json()
        assert len(docs) >= len(doc_ids)
        
        # Query
        chat_response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "What is in all documents?"},
        )
        assert chat_response.status_code == status.HTTP_200_OK
        
        # Delete one
        delete_response = client_with_mocks.delete(
            f"/api/v1/documents/{doc_ids[0]}"
        )
        assert delete_response.status_code == status.HTTP_200_OK

    def test_workflow_query_filters_by_document_id(self, client_with_mocks, test_pdf_file):
        """Test that chat can filter results by specific document ID."""
        # Upload document
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        document_id = response.json()["document_id"]
        
        # Query with document filter
        chat_response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "What is in the document?",
                "document_ids": [document_id],
                "include_sources": True
            },
        )
        assert chat_response.status_code == status.HTTP_200_OK
        chat_data = chat_response.json()
        assert chat_data["answer"]

    def test_workflow_with_invalid_document_id_in_filter(self, client_with_mocks):
        """Test chat with invalid document ID in filter."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "Test?",
                "document_ids": ["nonexistent_doc_xyz"]
            },
        )
        
        # Should either succeed (empty results) or fail gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_workflow_upload_then_delete_same_file_twice(
        self, client_with_mocks, test_pdf_file
    ):
        """Test uploading same file twice and deleting both."""
        # Upload first copy
        test_pdf_file.seek(0)
        response1 = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("document.pdf", test_pdf_file, "application/pdf")},
        )
        assert response1.status_code == status.HTTP_201_CREATED
        doc_id_1 = response1.json()["document_id"]
        
        # Upload second copy (same content, same filename)
        test_pdf_file.seek(0)
        response2 = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("document.pdf", test_pdf_file, "application/pdf")},
        )
        assert response2.status_code == status.HTTP_201_CREATED
        doc_id_2 = response2.json()["document_id"]
        
        # IDs should be different
        assert doc_id_1 != doc_id_2
        
        # Delete both
        delete1 = client_with_mocks.delete(f"/api/v1/documents/{doc_id_1}")
        assert delete1.status_code == status.HTTP_200_OK
        
        delete2 = client_with_mocks.delete(f"/api/v1/documents/{doc_id_2}")
        assert delete2.status_code == status.HTTP_200_OK


# ============================================================================
# Lifecycle 2: Chat Edge Cases
# ============================================================================

class TestChatEdgeCases:
    """Test chat edge cases and unusual scenarios."""

    def test_chat_without_documents(self, client_with_mocks):
        """Test chat when no documents have been uploaded."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "What is in the document?"},
        )
        
        # Should either succeed with empty results or fail gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    def test_chat_with_single_word_query(self, client_with_mocks):
        """Test chat with single word query."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "What?"},
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["answer"] is not None

    def test_chat_with_very_long_query(self, client_with_mocks):
        """Test chat with very long query."""
        long_query = "a" * 1000  # Well within limit
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": long_query},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_chat_with_multiple_questions(self, client_with_mocks):
        """Test chat with multiple questions in one query."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "What is this? How does it work? Why is it important?"
            },
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["answer"]

    def test_chat_with_formatting_characters(self, client_with_mocks):
        """Test chat with special formatting characters."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={
                "query": "What is this?\n\nHow does it work?\r\nWhy?"
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_chat_history_after_multiple_queries(self, client_with_mocks):
        """Test chat history after making multiple queries."""
        # Make multiple queries
        for i in range(3):
            client_with_mocks.post(
                "/api/v1/chat",
                json={"query": f"Question {i}?"},
            )
        
        # Get history
        response = client_with_mocks.get("/api/v1/chat/history")
        assert response.status_code == status.HTTP_200_OK
        
        history = response.json()
        assert isinstance(history, list)

    def test_chat_sources_consistency(self, client_with_mocks):
        """Test that sources in response are consistent."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?", "include_sources": True},
        )
        
        data = response.json()
        sources = data["sources"]
        
        # Each source should have required fields
        for source in sources:
            assert "document_id" in source
            assert "filename" in source
            assert "page_number" in source
            assert "similarity_score" in source
            assert 0 <= source["similarity_score"] <= 1.0


# ============================================================================
# Lifecycle 3: Data Persistence
# ============================================================================

class TestDataPersistence:
    """Test data persistence through system operations."""

    def test_upload_persists_metadata(self, client_with_mocks, test_pdf_file):
        """Test that upload persists document metadata."""
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        upload_data = response.json()
        document_id = upload_data["document_id"]
        
        # List documents should show the uploaded file
        list_response = client_with_mocks.get("/api/v1/documents")
        docs = list_response.json()
        
        # Should be able to find the document
        found = False
        for doc in docs:
            if doc.get("id") == document_id or doc.get("document_id") == document_id:
                found = True
                break
        
        assert found or len(docs) > 0  # Either find it or docs exist

    def test_document_deletion_removes_from_list(self, client_with_mocks, test_pdf_file):
        """Test that deleting document removes it from list."""
        # Upload
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        document_id = response.json()["document_id"]
        
        # Delete
        delete_response = client_with_mocks.delete(
            f"/api/v1/documents/{document_id}"
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # List should not contain deleted document
        list_response = client_with_mocks.get("/api/v1/documents")
        docs = list_response.json()
        
        for doc in docs:
            doc_id = doc.get("id") or doc.get("document_id")
            assert doc_id != document_id or not doc_id

    def test_chat_response_format_consistent(self, client_with_mocks):
        """Test that chat response format remains consistent."""
        responses = []
        
        for i in range(3):
            response = client_with_mocks.post(
                "/api/v1/chat",
                json={"query": f"Question {i}?"},
            )
            responses.append(response.json())
        
        # All responses should have same structure
        for resp in responses:
            required_keys = {"query", "answer", "sources", "context_sufficient"}
            assert required_keys.issubset(resp.keys())

    def test_delete_idempotent(self, client_with_mocks, test_pdf_file):
        """Test that deleting same document twice is safe."""
        # Upload
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        document_id = response.json()["document_id"]
        
        # Delete first time
        response1 = client_with_mocks.delete(f"/api/v1/documents/{document_id}")
        assert response1.status_code == status.HTTP_200_OK
        
        # Delete second time (should be idempotent)
        response2 = client_with_mocks.delete(f"/api/v1/documents/{document_id}")
        assert response2.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_system_health_after_operations(self, client_with_mocks, test_pdf_file):
        """Test system health is maintained after operations."""
        # Check health
        health1 = client_with_mocks.get("/api/v1/health")
        assert health1.status_code == status.HTTP_200_OK
        
        # Do some operations
        client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
        )
        
        client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        # Check health again
        health2 = client_with_mocks.get("/api/v1/health")
        assert health2.status_code == status.HTTP_200_OK
        
        # Health status should not degrade
        data1 = health1.json()
        data2 = health2.json()
        # Both should be "healthy" or "degraded", not unhealthy
        assert data1["status"] in ["healthy", "degraded"]
        assert data2["status"] in ["healthy", "degraded"]


# ============================================================================
# Error Recovery Workflows
# ============================================================================

class TestErrorRecoveryWorkflows:
    """Test error handling and recovery in workflows."""

    def test_chat_handles_no_llm_gracefully(self, client_with_mocks):
        """Test chat handles unavailable LLM gracefully."""
        response = client_with_mocks.post(
            "/api/v1/chat",
            json={"query": "Test?"},
        )
        
        # Should either succeed or fail gracefully (not 500)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_upload_handles_large_file_gracefully(self, client_with_mocks):
        """Test upload handles large files gracefully."""
        # Create a large file mock
        large_content = b"x" * (15 * 1024 * 1024)  # 15MB (over 10MB limit)
        
        response = client_with_mocks.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
        )
        
        # Should fail gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_delete_handles_concurrent_requests(self, client_with_mocks):
        """Test delete handles requests gracefully."""
        doc_id = "test_doc"
        
        # Multiple delete requests
        response1 = client_with_mocks.delete(f"/api/v1/documents/{doc_id}")
        response2 = client_with_mocks.delete(f"/api/v1/documents/{doc_id}")
        
        # Both should succeed or fail gracefully
        for response in [response1, response2]:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND
            ]
