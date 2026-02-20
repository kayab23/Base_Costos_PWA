import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "db_status" in data
    assert data["status"] in ["ok", "degraded"]

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "requests_total" in response.text
    assert "errors_total" in response.text
    assert "uptime_seconds" in response.text
