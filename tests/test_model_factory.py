from mirror.models.factory import generate_with_backend

def test_generate_with_backend_openai(monkeypatch):
    monkeypatch.setenv("MIRROR_MODEL_BACKEND", "openai")

    def fake_generate(prompt, model=None):
        return "ok"

    monkeypatch.setattr(
        "mirror.models.factory.generate_with_openai",
        fake_generate,
    )

    result = generate_with_backend("hello")

    assert result == "ok"
