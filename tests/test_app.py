from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root_returns_service_metadata():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"


def test_healthcheck_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
