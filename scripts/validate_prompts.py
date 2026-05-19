from __future__ import annotations

import sys
import tomllib
from pathlib import Path


PROMPTS_DIR = Path("prompts")
REGISTRY_PATH = PROMPTS_DIR / "registry.toml"



REQUIRED_PROMPTS = {
    "ocr_structuring": [
        "Return valid JSON only",
        "raw_text",
        "sections",
    ],
    "recommendation_report": ["{transcript}"],
    "homework_analysis": ["{transcript}"],
    "cleanup_json_repair": [],
    "cleanup_scaffold_single_mode": [],
}


def fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"✓ {message}")


def main() -> None:
    if not REGISTRY_PATH.exists():
        fail(f"Missing prompt registry: {REGISTRY_PATH}")

    with REGISTRY_PATH.open("rb") as file:
        registry = tomllib.load(file)

    if not isinstance(registry, dict):
        fail("Prompt registry is not a TOML table")

    for prompt_name, required_strings in REQUIRED_PROMPTS.items():
        if prompt_name not in registry:
            fail(f"Missing required prompt in registry: {prompt_name}")

        prompt_entry = registry[prompt_name]
        if not isinstance(prompt_entry, dict):
            fail(f"Invalid registry entry for prompt: {prompt_name}")

        active = str(prompt_entry.get("active", "")).strip()
        if not active:
            fail(f"Prompt {prompt_name} has no active version")

        versions = prompt_entry.get("versions", {})
        if not isinstance(versions, dict):
            fail(f"Prompt {prompt_name} has no versions table")

        active_entry = versions.get(active)
        if not isinstance(active_entry, dict):
            fail(f"Prompt {prompt_name} active version {active!r} is not defined")

        relative_file = active_entry.get("file")
        if not relative_file:
            fail(f"Prompt {prompt_name} version {active} has no file")

        prompt_path = PROMPTS_DIR / str(relative_file)
        if not prompt_path.exists():
            fail(f"Prompt file does not exist: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8").strip()
        if not content:
            fail(f"Prompt file is empty: {prompt_path}")

        for required in required_strings:
            if required not in content:
                fail(f"Prompt {prompt_name} is missing required text: {required!r}")

        ok(f"{prompt_name}:{active} -> {prompt_path} ({len(content)} chars)")

    ok("Prompt registry validation passed")


if __name__ == "__main__":
    main()
