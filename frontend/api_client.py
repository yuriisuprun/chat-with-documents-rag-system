"""
API Client for communication with the backend.

Provides methods to interact with the RAG system API endpoints.
"""

import logging
from typing import Any, Optional

import requests

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            raise Exception("Request timed out. The LLM may be processing.")
        except requests.HTTPError as e:
            try:
                error_detail = e.response.json()
                raise Exception(f"API Error: {error_detail.get('detail', str(e))}")
            except Exception:
                raise Exception(
                    f"API Error: {e.response.status_code} {e.response.reason}"
                )
        except Exception as e:
            # Include full exception details for debugging
            import traceback
            tb = traceback.format_exc()
            raise Exception(f"Connection error: {str(e)}\n{tb}")

    def upload_document(self, file_obj: Any) -> dict:
        """
        Upload a PDF document.

        Args:
            file_obj: Streamlit UploadedFile object

        Returns:
            DocumentUploadResponse
        """
        logger.info(f"Starting PDF upload: {file_obj.name}")
        logger.debug(f"File object type: {type(file_obj)}")
        
        try:
            # Streamlit UploadedFile has different behavior than regular files
            logger.debug("Reading file content into bytes...")
            
            # Method 1: Try file_obj.read() - the standard way
            if hasattr(file_obj, 'getvalue') and callable(file_obj.getvalue):
                # UploadedFile inherits from BytesIO, use getvalue() for efficiency
                logger.debug("Using file_obj.getvalue() (BytesIO method)")
                content = file_obj.getvalue()
            elif hasattr(file_obj, 'read') and callable(file_obj.read):
                logger.debug("Using file_obj.read()")
                # Reset pointer first
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                content = file_obj.read()
            else:
                raise ValueError(f"Cannot read file from object of type {type(file_obj)}")
            
            # CRITICAL: Ensure content is bytes, not memoryview or other buffer type
            if isinstance(content, memoryview):
                logger.debug("Content is memoryview, converting to bytes")
                content = bytes(content)
            elif not isinstance(content, bytes):
                logger.debug(f"Content type is {type(content)}, converting to bytes")
                content = bytes(content)
            
            logger.info(f"File read successfully. Size: {len(content)} bytes")
            logger.debug(f"Final content type: {type(content)}")
            
            url = f"{self.base_url}/api/v1/documents/upload"
            logger.info(f"Uploading to: {url}")
            
            # Use requests library with bytes directly (not file-like object)
            # This prevents requests from trying to call .read() on our object
            files = {
                "file": (file_obj.name, content, "application/pdf")
            }
            logger.debug(f"Files dict created with name: {file_obj.name}")
            
            logger.debug("Sending POST request with requests library...")
            response = requests.post(url, files=files, timeout=self.timeout)
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code >= 400:
                logger.error(f"Response text: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Upload successful. Document ID: {result.get('document_id')}")
            logger.debug(f"Full response: {result}")
            return result
                
        except requests.HTTPError as e:
            logger.error(f"HTTP Status Error: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            try:
                error_detail = e.response.json()
                detail = error_detail.get('detail', str(e))
            except Exception:
                detail = e.response.text
            raise Exception(f"Upload failed: {detail}")
            
        except Exception as e:
            logger.exception(f"Unexpected error during upload: {type(e).__name__}: {str(e)}")
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Traceback:\n{tb}")
            raise Exception(f"Upload failed: {str(e)}")

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
