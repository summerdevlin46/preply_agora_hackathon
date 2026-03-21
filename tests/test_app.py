import importlib
import sqlite3
import types
import builtins
import sys
import json

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


def test_report_analyze_returns_503_when_audio_dependency_is_missing(monkeypatch):
    original_import = builtins.__import__

    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "thymia_sentinel":
            raise ModuleNotFoundError(
                "No module named 'thymia_sentinel'",
                name="thymia_sentinel",
            )
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", failing_import)

    response = client.post(
        "/api/report/analyze",
        files={"wav_file": ("session.wav", b"RIFF", "audio/wav")},
        data={"chat_id": "chat-missing-dep", "transcript": "hello"},
    )

    assert response.status_code == 503
    assert "optional dependency is missing" in response.json()["detail"]
    assert "thymia_sentinel" in response.json()["detail"]


def test_report_analyze_returns_503_when_thymia_api_key_is_missing(monkeypatch):
    async def fake_run_analysis(chat_id: str, wav_path: str, transcript: str = ""):
        raise ValueError("THYMIA_API_KEY environment variable or api_key parameter required")

    monkeypatch.setitem(
        sys.modules,
        "mirror.analysis.thymia_service",
        types.SimpleNamespace(analyze_session=fake_run_analysis),
    )

    response = client.post(
        "/api/report/analyze",
        files={"wav_file": ("session.wav", b"RIFF", "audio/wav")},
        data={"chat_id": "chat-missing-thymia-key", "transcript": "hello"},
    )

    assert response.status_code == 503
    assert "THYMIA_API_KEY" in response.json()["detail"]


def test_connect_sentinel_sends_config_event(monkeypatch):
    thymia_service = importlib.import_module("mirror.analysis.thymia_service")

    sent_messages = []

    class FakeWebSocket:
        async def send(self, message):
            sent_messages.append(message)

    async def fake_connect(url, max_size=None):
        assert url == "wss://ws.thymia.ai"
        return FakeWebSocket()

    created_tasks = []

    def fake_create_task(coro):
        created_tasks.append(coro)

        class FakeTask:
            def cancel(self):
                return None

        return FakeTask()

    monkeypatch.setattr(thymia_service.websockets, "connect", fake_connect)
    monkeypatch.setattr(thymia_service.asyncio, "create_task", fake_create_task)

    sentinel = thymia_service.SentinelClient(
        api_key="test-thymia-key",
        user_label="mirror-session-analysis",
        biomarkers=["helios"],
        sample_rate=16000,
    )

    import asyncio
    asyncio.run(thymia_service._connect_sentinel(sentinel))

    assert sentinel.connected is True
    assert sent_messages
    first_message = json.loads(sent_messages[0])
    assert first_message["type"] == "CONFIG"
    assert first_message["api_key"] == "test-thymia-key"
    assert first_message["audio_config"]["sample_rate"] == 16000
    assert created_tasks

    for coro in created_tasks:
        coro.close()
