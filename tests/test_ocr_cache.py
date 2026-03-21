from pathlib import Path

from mirror.ocr.cache import build_cache_key, file_sha256, load_cached_parse, save_cached_parse


def test_file_sha256_returns_value(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world")

    result = file_sha256(file_path)

    assert isinstance(result, str)
    assert len(result) == 64


def test_build_cache_key_is_stable(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("same content")

    key1 = build_cache_key(file_path, model="gpt-4o-mini", prompt_version="v1")
    key2 = build_cache_key(file_path, model="gpt-4o-mini", prompt_version="v1")

    assert key1 == key2


def test_save_and_load_cached_parse(tmp_path: Path, monkeypatch):
    from mirror.ocr import cache as cache_module

    monkeypatch.setattr(cache_module, "CACHE_DIR", tmp_path / ".cache")

    key = "abc123"
    payload = {"title": "Test Worksheet", "topic": "grammar"}

    save_cached_parse(key, payload)
    loaded = load_cached_parse(key)

    assert loaded == payload
