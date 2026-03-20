from mirror.models.factory import generate_with_backend


def test_invalid_backend(monkeypatch):
    monkeypatch.setenv("MIRROR_MODEL_BACKEND", "banana")
    result = generate_with_backend("hello")
    assert "Invalid model backend" in result


def test_openai_backend_dispatch(monkeypatch):
    monkeypatch.setenv("MIRROR_MODEL_BACKEND", "openai")

    def fake_openai(prompt: str, model=None) -> str:
        return "openai-ok"

    monkeypatch.setattr("mirror.models.factory.generate_with_openai", fake_openai)

    result = generate_with_backend("hello")
    assert result == "openai-ok"


def test_huggingface_backend_dispatch(monkeypatch):
    monkeypatch.setenv("MIRROR_MODEL_BACKEND", "huggingface")

    def fake_hf(prompt: str, model=None) -> str:
        return "hf-ok"

    monkeypatch.setattr("mirror.models.factory.generate_with_huggingface", fake_hf)

    result = generate_with_backend("hello")
    assert result == "hf-ok"


def test_backend_failure_returns_message(monkeypatch):
    monkeypatch.setenv("MIRROR_MODEL_BACKEND", "huggingface")

    def fake_hf(prompt: str, model=None) -> str:
        raise RuntimeError("kaboom")

    monkeypatch.setattr("mirror.models.factory.generate_with_huggingface", fake_hf)

    result = generate_with_backend("hello")
    assert "failed" in result.lower()
    assert "kaboom" in result
