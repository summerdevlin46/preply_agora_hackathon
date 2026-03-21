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


def test_default_chat_instructions_returns_seeded_value():
    response = client.get("/api/chat/default-instructions")

    assert response.status_code == 200
    assert "instructions" in response.json()
    assert response.json()["instructions"]
