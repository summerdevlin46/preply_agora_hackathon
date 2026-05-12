from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mirror.models.model_config import get_model_config


DEFAULT_FALLBACK_FILE = "config/demo_fallbacks/cooking_present_continuous.json"


def _fallback_config() -> dict[str, Any]:
    config = get_model_config()
    generation = config.get("generation", {})

    if not isinstance(generation, dict):
        return {}

    fallback = generation.get("fallback", {})
    return fallback if isinstance(fallback, dict) else {}


def is_demo_fallback_enabled() -> bool:
    return bool(_fallback_config().get("enabled", False))


def demo_fallback_description() -> str:
    return str(
        _fallback_config().get(
            "description",
            "Demo fallback content.",
        )
    )


def load_demo_fallback() -> dict[str, Any]:
    path = Path(str(_fallback_config().get("file", DEFAULT_FALLBACK_FILE)))

    if not path.exists():
        raise RuntimeError(f"Demo fallback file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"Demo fallback file must contain a JSON object: {path}")

    return data


def demo_fallback_warning(error: str) -> str:
    return (
        "Exercise generation failed. "
        f"Serving demo fallback content. Fallback: {demo_fallback_description()}. "
        f"Original error: {error}"
    )
