from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_service_identity():
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "AQuantLens API",
        "status": "ok",
    }
