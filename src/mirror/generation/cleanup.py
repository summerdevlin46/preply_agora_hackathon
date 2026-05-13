"""
mirror/generation/cleanup.py

Generates worksheet-grounded avatar session prompts plus three
student-facing tasks per mode.

Fresh generation calls the configured model once per mode.
Targeted regeneration calls the model only for the selected mode.

Output keys match the frontend ASSIGNMENT_TYPES ids exactly:
  avatar_conversation, vocabulary_challenge, read_aloud_review, error_detective
"""
import json
import logging
from typing import Any

from mirror.generation.prompt_loader import load_prompt_spec
from mirror.models.factory import generate_with_backend
from mirror.utils.logging import preview_text

logger = logging.getLogger(__name__)

MODES = [
    "avatar_conversation",
    "vocabulary_challenge",
    "read_aloud_review",
    "error_detective",
]

CLEANUP_PROMPT_NAME = "cleanup_single_mode"
CLEANUP_PROMPT_SPEC = load_prompt_spec(CLEANUP_PROMPT_NAME)


def _build_user_message(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str | None = None,
) -> str:
    parts: list[str] = []

    if feedback:
        parts.append(
            "TEACHER FEEDBACK ON PREVIOUS VERSION:\n"
            f"{feedback.strip()}\n\n"
            "Revise this mode's prompt and tasks based on the feedback."
        )

    parts.append(f"MODE TO GENERATE:\n{mode}")
    parts.append(f"TEACHER NOTES:\n{teacher_notes.strip() or 'None provided.'}")
    parts.append(
        "WORKSHEET JSON:\n"
        f"{json.dumps(worksheet_json, ensure_ascii=False, indent=2)}"
    )

    return "\n\n".join(parts)


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()

    if not text.startswith("```"):
        return text

    parts = text.split("```")
    if len(parts) < 2:
        return text

    fenced = parts[1].strip()
    if fenced.lower().startswith("json"):
        fenced = fenced[4:].strip()

    return fenced


def _extract_json_object(raw: str) -> str:
    text = _strip_json_fences(raw)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return text

    return text[start : end + 1]


def _parse_single_mode_response(raw: str, mode: str) -> dict[str, Any]:
    text = _extract_json_object(raw)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(
            "Cleanup model returned invalid JSON for mode=%s:\n%s",
            mode,
            preview_text(raw),
        )
        raise RuntimeError(
            f"Cleanup model did not return valid JSON for mode '{mode}'."
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(f"Cleanup model did not return a JSON object for mode '{mode}'.")

    prompt = str(parsed.get("prompt", "")).strip()
    if not prompt:
        raise RuntimeError(f"Cleanup model returned empty or missing prompt for mode '{mode}'.")

    tasks = parsed.get("tasks", [])
    if not isinstance(tasks, list):
        raise RuntimeError(f"Cleanup model returned invalid tasks for mode '{mode}'.")

    if len(tasks) != 3:
        raise RuntimeError(f"Expected 3 tasks for mode '{mode}', got {len(tasks)}.")

    normalized_tasks: list[dict[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise RuntimeError(f"Task in mode '{mode}' is not an object: {task}")

        title = str(task.get("title", "")).strip()
        description = str(task.get("description", "")).strip()

        if not title or not description:
            raise RuntimeError(
                f"Task in mode '{mode}' missing title or description: {task}"
            )

        normalized_tasks.append(
            {
                "title": title,
                "description": description,
            }
        )

    return {
        "prompt": prompt,
        "tasks": normalized_tasks,
    }


def _run_single_mode(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}. Must be one of {MODES}")

    user_message = _build_user_message(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        mode=mode,
        feedback=feedback,
    )

    logger.info(
        "Running cleanup model prompt=%s version=%s sha=%s mode=%s feedback=%s",
        CLEANUP_PROMPT_SPEC.name,
        CLEANUP_PROMPT_SPEC.version,
        CLEANUP_PROMPT_SPEC.sha256[:12],
        mode,
        bool(feedback),
    )

    raw = generate_with_backend(
        prompt=user_message,
        task="cleanup",
        system_prompt=CLEANUP_PROMPT_SPEC.content,
    ).strip()

    return _parse_single_mode_response(raw, mode)


def run_cleanup(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
    mode: str | None = None,
    existing_prompts: dict | None = None,
) -> dict:
    """
    Fresh generation returns a dict with keys:
      avatar_conversation
      vocabulary_challenge
      read_aloud_review
      error_detective
      tasks

    If feedback + mode + existing_prompts are provided, this delegates to
    single-mode regeneration for backward compatibility with existing callers.
    """
    if feedback and mode and existing_prompts:
        return run_single_mode_regeneration(
            teacher_notes=teacher_notes,
            worksheet_json=worksheet_json,
            mode=mode,
            feedback=feedback,
            existing_prompts=existing_prompts,
        )

    result: dict[str, Any] = {}
    tasks: dict[str, list[dict[str, str]]] = {}

    for current_mode in MODES:
        mode_result = _run_single_mode(
            teacher_notes=teacher_notes,
            worksheet_json=worksheet_json,
            mode=current_mode,
        )
        result[current_mode] = mode_result["prompt"]
        tasks[current_mode] = mode_result["tasks"]

    return {
        **result,
        "tasks": tasks,
    }


def run_single_mode_regeneration(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str,
    existing_prompts: dict,
) -> dict:
    """
    Regenerates a single mode and returns the full output dict with all modes intact.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}. Must be one of {MODES}")

    updated = dict(existing_prompts or {})
    existing_tasks = updated.get("tasks", {})

    if not isinstance(existing_tasks, dict):
        existing_tasks = {}

    missing_existing_modes = [
        existing_mode
        for existing_mode in MODES
        if existing_mode != mode and not str(updated.get(existing_mode, "")).strip()
    ]
    if missing_existing_modes:
        raise RuntimeError(
            "Cannot regenerate a single mode without existing prompts for: "
            f"{missing_existing_modes}"
        )

    mode_result = _run_single_mode(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        mode=mode,
        feedback=feedback,
    )

    updated[mode] = mode_result["prompt"]
    updated["tasks"] = {
        **existing_tasks,
        mode: mode_result["tasks"],
    }

    return updated
