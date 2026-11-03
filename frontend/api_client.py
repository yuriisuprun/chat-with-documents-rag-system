"""
API Client for communication with the backend.

Provides methods to interact with the RAG system API endpoints.
"""

from typing import Any, Optional

import httpx


class APIClient:
    """Client for communicating with the backend API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 120.0  # 2 minutes for LLM responses

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise Exception("Request timed out. The LLM may be processing.")
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
                raise Exception(f"API Error: {error_detail.get('detail', str(e))}")
            except Exception:
                raise Exception(
                    f"API Error: {e.response.status_code} {e.response.reason_phrase}"
                )
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

    def upload_document(self, file_obj: Any) -> dict:
        """
        Upload a PDF document.

        Args:
            file_obj: Streamlit UploadedFile object

        Returns:
            DocumentUploadResponse
        """
        files = {"file": (file_obj.name, file_obj.getbuffer(), "application/pdf")}
        return self._make_request("POST", "/api/v1/documents/upload", files=files)

    def list_documents(self) -> dict:
        """
        Get list of indexed documents.

        Returns:
            DocumentListResponse with list of documents and count
        """
        return self._make_request("GET", "/api/v1/documents")

    def get_document(self, document_id: str) -> dict:
        """
        Get details of a specific document.

        Args:
            document_id: Document ID

        Returns:
            DocumentDetailResponse
        """
        return self._make_request("GET", f"/api/v1/documents/{document_id}")

    def delete_document(self, document_id: str) -> dict:
        """
        Delete a document.

        Args:
            document_id: Document ID to delete

        Returns:
            DocumentDeleteResponse
        """
        return self._make_request("DELETE", f"/api/v1/documents/{document_id}")

    def ask_question(
        self,
        query: str,
        document_ids: Optional[list[str]] = None,
        include_sources: bool = True,
    ) -> dict:
        """
        Ask a question about indexed documents.

        Args:
            query: User question
            document_ids: Optional list of document IDs to search
            include_sources: Whether to include source references

        Returns:
            ChatResponse with answer and sources
        """
        payload = {
            "query": query,
            "document_ids": document_ids,
            "include_sources": include_sources,
        }
        return self._make_request(
            "POST",
            "/api/v1/chat",
            json=payload,
        )

    def check_health(self) -> dict:
        """
        Check system health.

        Returns:
            HealthCheckResponse with service statuses
        """
        return self._make_request("GET", "/api/v1/health")
