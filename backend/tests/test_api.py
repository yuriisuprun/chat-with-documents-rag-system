"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)


class TestHealth:
    """Health check tests."""

    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_ready_check(self):
        """Test readiness endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] == True


class TestTenants:
    """Tenant management tests."""

    def test_create_tenant(self):
        """Test creating a tenant."""
        payload = {
            "business_name": "Test Law Firm",
            "professional_name": "John Doe",
            "whatsapp_number": "+1234567890",
            "auto_reply_delay_minutes": 30,
            "booking_url": "https://calendly.com/john",
            "disclaimer": "This is not legal advice."
        }
        response = client.post("/api/v1/tenants", json=payload)
        assert response.status_code == 201
        assert response.json()["business_name"] == "Test Law Firm"
        assert "id" in response.json()

    def test_get_tenant(self):
        """Test getting a tenant."""
        # Create first
        payload = {
            "business_name": "Test Firm",
            "professional_name": "Jane Doe",
            "whatsapp_number": "+0987654321",
        }
        create_response = client.post("/api/v1/tenants", json=payload)
        tenant_id = create_response.json()["id"]

        # Get
        response = client.get(f"/api/v1/tenants/{tenant_id}")
        assert response.status_code == 200
        assert response.json()["id"] == tenant_id

    def test_list_tenants(self):
        """Test listing tenants."""
        response = client.get("/api/v1/tenants")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestConversations:
    """Conversation tests."""

    @pytest.fixture
    def tenant(self):
        """Create test tenant."""
        payload = {
            "business_name": "Test Firm",
            "professional_name": "Test Pro",
            "whatsapp_number": "+1111111111",
        }
        response = client.post("/api/v1/tenants", json=payload)
        return response.json()

    def test_list_conversations(self, tenant):
        """Test listing conversations."""
        response = client.get(
            f"/api/v1/conversations?tenant_id={tenant['id']}"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
