from pathlib import Path

from mirror.ocr.vision_parser import parse_worksheet_to_json


class DummyResponse:
    output_text = """
    {
      "title": "Test Worksheet",
      "worksheet_type": "Grammar Worksheet",
      "level": "A1",
      "topic": "Past Simple",
      "instructions": ["Complete the sentences."],
      "sections": [],
      "answer_key": [],
      "notes": [],
      "raw_text": "Complete the sentences."
    }
    """.strip()


class DummyClient:
    class responses:
        call_count = 0

        @staticmethod
        def create(**kwargs):
            DummyClient.responses.call_count += 1
            return DummyResponse()


def test_parse_worksheet_to_json_for_image(monkeypatch, tmp_path: Path):
    file_path = tmp_path / "sample.png"
    file_path.write_bytes(b"fake-image")

    monkeypatch.setattr("mirror.ocr.vision_parser.OpenAI", lambda api_key=None: DummyClient())
    monkeypatch.setattr("mirror.ocr.vision_parser.image_file_to_data_url", lambda path: "data:image/png;base64,abc")

    result = parse_worksheet_to_json(str(file_path))

    assert result["title"] == "Test Worksheet"
    assert result["topic"] == "Past Simple"


def test_parse_worksheet_to_json_uses_cache_on_second_call(monkeypatch, tmp_path: Path):
    from mirror.ocr import cache as cache_module
    from mirror.ocr import vision_parser as vp

    file_path = tmp_path / "sample.png"
    file_path.write_bytes(b"fake-image")

    monkeypatch.setattr(cache_module, "CACHE_DIR", tmp_path / ".cache")
    monkeypatch.setattr(vp, "OpenAI", lambda api_key=None: DummyClient())
    monkeypatch.setattr(vp, "image_file_to_data_url", lambda path: "data:image/png;base64,abc")

    DummyClient.responses.call_count = 0

    result1 = parse_worksheet_to_json(str(file_path))
    result2 = parse_worksheet_to_json(str(file_path))

    assert result1["title"] == "Test Worksheet"
    assert result2["title"] == "Test Worksheet"
    assert DummyClient.responses.call_count == 1
