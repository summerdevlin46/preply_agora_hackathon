from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


PROMPTS_DIR = Path("prompts")
REGISTRY_PATH = PROMPTS_DIR / "registry.toml"


@dataclass(frozen=True)
class PromptSpec:
    name: str
    version: str
    path: Path
    content: str
    sha256: str
    description: str = ""
    notes: str = ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise RuntimeError(f"Prompt registry not found: {REGISTRY_PATH}")

    with REGISTRY_PATH.open("rb") as file:
        return tomllib.load(file)


@lru_cache(maxsize=128)
def load_prompt_spec(name: str, version: str | None = None) -> PromptSpec:
    registry = _load_registry()

    if name not in registry:
        raise RuntimeError(f"Prompt {name!r} not found in {REGISTRY_PATH}")

    prompt_entry = registry[name]
    if not isinstance(prompt_entry, dict):
        raise RuntimeError(f"Invalid prompt registry entry for {name!r}")

    selected_version = version or str(prompt_entry.get("active", "")).strip()
    if not selected_version:
        raise RuntimeError(f"No active version configured for prompt {name!r}")

    versions = prompt_entry.get("versions", {})
    version_entry = versions.get(selected_version)

    if not isinstance(version_entry, dict):
        raise RuntimeError(
            f"Prompt {name!r} version {selected_version!r} not found in registry."
        )

    relative_file = version_entry.get("file")
    if not relative_file:
        raise RuntimeError(
            f"Prompt {name!r} version {selected_version!r} has no file configured."
        )

    path = PROMPTS_DIR / str(relative_file)

    if not path.exists():
        raise RuntimeError(f"Prompt file not found: {path}")

    content = path.read_text(encoding="utf-8").strip()

    return PromptSpec(
        name=name,
        version=selected_version,
        path=path,
        content=content,
        sha256=_sha256(content),
        description=str(prompt_entry.get("description", "")),
        notes=str(version_entry.get("notes", "")),
    )


def load_prompt(name: str, version: str | None = None) -> str:
    return load_prompt_spec(name, version).content