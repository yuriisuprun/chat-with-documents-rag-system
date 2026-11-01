"""
Test application startup and health endpoint.

Verifies that the FastAPI application initializes correctly and responds to requests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_app_startup():
    """Test that the app can be created."""
    app = create_app()
    assert app is not None
    assert app.title == "Chat With Documents – RAG System"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["api_version"] == "v1"


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "version" in data
    assert "timestamp" in data
    assert data["status"] in ("healthy", "degraded", "unhealthy")


def test_openapi_docs(client):
    """Test that OpenAPI documentation is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


def test_invalid_route(client):
    """Test that invalid routes return 404."""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
