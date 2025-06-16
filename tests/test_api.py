import pytest
import sys
import os

# Add the pypkg directory to the path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../imageroot/pypkg'))

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    from mailwebhook.main import app
    
    return TestClient(app)

def test_status_endpoint(client):
    """Test the status endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["status"] == "healthy"

def test_schedules_list_empty(client):
    """Test listing schedules when none exist"""
    response = client.get("/api/schedules/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_schedule(client):
    """Test creating a new schedule"""
    schedule_data = {
        "mailbox_to_monitor": "test@example.com",
        "webhook_url": "https://example.com/webhook",
        "payload_format": "JSON",
        "is_active": True
    }
    
    response = client.post("/api/schedules/", json=schedule_data)
    assert response.status_code == 201
    data = response.json()
    assert data["mailbox_to_monitor"] == "test@example.com"
    assert data["webhook_url"] == "https://example.com/webhook"

def test_logs_endpoint(client):
    """Test the logs endpoint"""
    response = client.get("/api/logs/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
