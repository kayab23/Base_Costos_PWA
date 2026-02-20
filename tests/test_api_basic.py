from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["db_status"] in ("ok", "error")

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "requests_total" in response.text
    assert "errors_total" in response.text
