import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".cache/worksheet_parses")


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def clear_cache() -> None:
    _ensure_cache_dir()
    for file in CACHE_DIR.glob("*.json"):
        file.unlink()


def build_cache_key(path: Path, model: str, prompt_version: str) -> str:
    file_hash = file_sha256(path)
    raw = f"{file_hash}:{model}:{prompt_version}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_cached_parse(cache_key: str) -> dict[str, Any] | None:
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if not cache_file.exists():
        return None
    return json.loads(cache_file.read_text(encoding="utf-8"))


def save_cached_parse(cache_key: str, data: dict[str, Any]) -> None:
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{cache_key}.json"
    cache_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
