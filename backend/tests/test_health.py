from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_live_health_returns_ok() -> None:
    response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_returns_service_shape() -> None:
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert set(response.json().keys()) == {"status", "redis"}
