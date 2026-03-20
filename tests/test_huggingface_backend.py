from huggingface_hub.errors import BadRequestError
from mirror.models.huggingface_backend import generate_with_huggingface


class DummyMessage:
    def __init__(self, content: str):
        self.content = content


class DummyChoice:
    def __init__(self, content: str):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


def test_hf_uses_selected_model(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "fake-token")
    monkeypatch.setenv("HF_MODEL", "some/model")

    calls = []

    class DummyClient:
        def __init__(self, api_key=None):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    calls.append(kwargs)
                    return DummyResponse("ok")

    monkeypatch.setattr("mirror.models.huggingface_backend.InferenceClient", DummyClient)

    result = generate_with_huggingface("hello")
    assert result == "ok"
    assert calls[0]["model"] == "some/model"


def test_hf_retries_without_model_if_model_not_supported(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "fake-token")
    monkeypatch.setenv("HF_MODEL", "unsupported/model")

    calls = []

    class FakeHTTPRequest:
        method = "POST"
        url = "https://router.huggingface.co/v1/chat/completions"

    class FakeHTTPResponse:
        status_code = 400
        text = "model_not_supported"
        headers = {}
        request = FakeHTTPRequest()

    class DummyClient:
        def __init__(self, api_key=None):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    calls.append(kwargs)
                    if "model" in kwargs:
                        raise BadRequestError(
                            "model_not_supported",
                            response=FakeHTTPResponse(),
                        )
                    return DummyResponse("fallback-ok")

    monkeypatch.setattr("mirror.models.huggingface_backend.InferenceClient", DummyClient)

    result = generate_with_huggingface("hello")
    assert result == "fallback-ok"
    assert "model" in calls[0]
    assert "model" not in calls[1]
