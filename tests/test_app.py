import importlib
import sqlite3
import types

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
    response = client.get("/api/chat/get-user-chat-instructions")
    assert response.status_code == 200
    assert "instructions" in response.json()
    assert response.json()["instructions"]


def test_complete_homework_persists_wrap_and_marks_chat_complete(tmp_path, monkeypatch):
    db_path = tmp_path / "mirror.sqlite3"
    monkeypatch.setenv("MIRROR_CONFIG_DB_PATH", str(db_path))

    config_store = importlib.import_module("mirror.api.config_store")
    config_store.initialize_config_db()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO chat_config (
                id,
                tutorId,
                studentId,
                anamPrompt,
                completionState
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("chat-123", "tutor-1", "student-1", "Prompt", "false"),
        )
        connection.commit()

    class FakeResponses:
        @staticmethod
        def create(model: str, input: str):
            assert model == "gpt-5"
            assert "1. USER: I goed to Paris" in input

            class Response:
                output_text = (
                    "Overall outcome: The student completed the task.\n"
                    "Strengths: Stayed engaged.\n"
                    "- Struggled with proper nouns in line 1.\n"
                    "Recommended follow-up: Review names and places."
                )

            return Response()

    class FakeOpenAI:
        def __init__(self, api_key: str):
            assert api_key == "test-key"
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(
        __import__("sys").modules,
        "openai",
        types.SimpleNamespace(OpenAI=FakeOpenAI),
    )

    response = client.post(
        "/api/chat/chat-123/complete",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "I goed to Paris",
                    "interrupted": False,
                },
                {
                    "role": "persona",
                    "content": "You should say went.",
                    "interrupted": False,
                },
            ]
        },
    )

    assert response.status_code == 200
    assert "Overall outcome" in response.json()["analysis"]

    with sqlite3.connect(db_path) as connection:
        wrapped = connection.execute(
            "SELECT transcript, analysis FROM homework_wrapped WHERE chatId = ?",
            ("chat-123",),
        ).fetchone()
        completion_state = connection.execute(
            "SELECT completionState FROM chat_config WHERE id = ?",
            ("chat-123",),
        ).fetchone()

    assert wrapped is not None
    assert "1. USER: I goed to Paris" in wrapped[0]
    assert "proper nouns" in wrapped[1]
    assert completion_state == ("true",)


def test_complete_homework_falls_back_when_openai_is_unavailable(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "mirror.sqlite3"
    monkeypatch.setenv("MIRROR_CONFIG_DB_PATH", str(db_path))

    config_store = importlib.import_module("mirror.api.config_store")
    config_store.initialize_config_db()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO chat_config (
                id,
                tutorId,
                studentId,
                anamPrompt,
                completionState
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("chat-fallback", "tutor-1", "student-1", "Prompt", "false"),
        )
        connection.commit()

    service = importlib.import_module("mirror.api.service")
    monkeypatch.setattr(
        service,
        "_generate_homework_analysis",
        lambda transcript: (_ for _ in ()).throw(
            RuntimeError("simulated OpenAI outage")
        ),
    )

    response = client.post(
        "/api/chat/chat-fallback/complete",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "I am cook dinner now",
                    "interrupted": False,
                },
                {
                    "role": "persona",
                    "content": "Try adding the missing -ing form.",
                    "interrupted": False,
                },
            ]
        },
    )

    assert response.status_code == 200
    assert "fallback was used" in response.json()["analysis"]

    with sqlite3.connect(db_path) as connection:
        wrapped = connection.execute(
            "SELECT transcript, analysis FROM homework_wrapped WHERE chatId = ?",
            ("chat-fallback",),
        ).fetchone()
        completion_state = connection.execute(
            "SELECT completionState FROM chat_config WHERE id = ?",
            ("chat-fallback",),
        ).fetchone()

    assert wrapped is not None
    assert "1. USER: I am cook dinner now" in wrapped[0]
    assert "simulated OpenAI outage" in wrapped[1]
    assert completion_state == ("true",)
