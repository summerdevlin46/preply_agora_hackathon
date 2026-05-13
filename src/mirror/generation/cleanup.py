"""
mirror/generation/cleanup.py

Generates four worksheet-grounded avatar session prompts plus three
student-facing tasks per mode.

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

CLEANUP_PROMPT_NAME = "cleanup_avatar_prompts"
CLEANUP_PROMPT_SPEC = load_prompt_spec(CLEANUP_PROMPT_NAME)


def build_cleanup_user_message(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
    mode: str | None = None,
) -> str:
    parts: list[str] = []

    if feedback and mode:
        parts.append(
            f"TEACHER FEEDBACK ON PREVIOUS VERSION OF '{mode}':\n"
            f"{feedback.strip()}\n\n"
            f"Please revise only the '{mode}' prompt and its tasks based on this feedback. "
            f"Return the full JSON for all four modes. Keep the other modes unchanged "
            f"unless they are required to keep the output schema valid."
        )

    parts.append(f"TEACHER NOTES:\n{teacher_notes.strip() or 'None provided.'}")
    parts.append(f"WORKSHEET JSON:\n{json.dumps(worksheet_json, ensure_ascii=False, indent=2)}")

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


def _parse_cleanup_json(raw: str) -> dict[str, Any]:
    text = _extract_json_object(raw)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Cleanup model returned invalid JSON:\n%s", preview_text(raw))
        raise RuntimeError("Cleanup model did not return valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Cleanup model did not return a JSON object.")

    return parsed


def _validate_task(task: Any, mode: str) -> dict[str, str]:
    if not isinstance(task, dict):
        raise RuntimeError(f"Task in mode '{mode}' is not an object: {task}")

    title = str(task.get("title", "")).strip()
    description = str(task.get("description", "")).strip()

    if not title or not description:
        raise RuntimeError(f"Task in mode '{mode}' missing title or description: {task}")

    return {
        "title": title,
        "description": description,
    }


def _validate_cleanup_output(
    parsed: dict[str, Any],
    *,
    existing_prompts: dict | None = None,
) -> dict[str, Any]:
    missing = [mode for mode in MODES if mode not in parsed]

    if missing:
        if existing_prompts:
            for mode in missing:
                existing_value = existing_prompts.get(mode)
                if existing_value:
                    parsed[mode] = existing_value
                    logger.info("Preserved existing prompt for mode: %s", mode)

        still_missing = [mode for mode in MODES if mode not in parsed]
        if still_missing:
            raise RuntimeError(f"Cleanup model missing modes: {still_missing}")

    prompts: dict[str, str] = {}

    for mode in MODES:
        prompt = str(parsed.get(mode, "")).strip()
        if not prompt:
            raise RuntimeError(f"Cleanup model returned empty prompt for mode '{mode}'.")
        prompts[mode] = prompt

    raw_tasks = parsed.get("tasks", {})
    if not isinstance(raw_tasks, dict):
        raise RuntimeError("Cleanup model returned invalid tasks object.")

    tasks: dict[str, list[dict[str, str]]] = {}

    for mode in MODES:
        mode_tasks = raw_tasks.get(mode, [])

        if not isinstance(mode_tasks, list):
            raise RuntimeError(f"Tasks for mode '{mode}' are not a list.")

        if len(mode_tasks) != 3:
            raise RuntimeError(f"Expected 3 tasks for mode '{mode}', got {len(mode_tasks)}.")

        tasks[mode] = [_validate_task(task, mode) for task in mode_tasks]

    return {
        **prompts,
        "tasks": tasks,
    }


def run_cleanup(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
    mode: str | None = None,
    existing_prompts: dict | None = None,
) -> dict:
    """
    Returns a dict with keys:
      avatar_conversation
      vocabulary_challenge
      read_aloud_review
      error_detective
      tasks

    Fresh generation produces all four modes in one call.

    Regeneration still asks for full JSON, but includes teacher feedback telling
    the model which mode to revise. This avoids introducing a separate single-mode
    generation path before the overall workflow is stable.
    """
    user_message = build_cleanup_user_message(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
        mode=mode,
    )

    logger.info(
        "Running cleanup model via configured provider prompt=%s version=%s sha=%s "
        "(feedback=%s, mode=%s)",
        CLEANUP_PROMPT_SPEC.name,
        CLEANUP_PROMPT_SPEC.version,
        CLEANUP_PROMPT_SPEC.sha256[:12],
        bool(feedback),
        mode,
    )

    raw = generate_with_backend(
        prompt=user_message,
        task="exercise",
        system_prompt=CLEANUP_PROMPT_SPEC.content,
    ).strip()

    parsed = _parse_cleanup_json(raw)

    return _validate_cleanup_output(
        parsed,
        existing_prompts=existing_prompts,
    )


def run_single_mode_regeneration(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str,
    existing_prompts: dict,
) -> dict:
    """
    Regenerates a single mode by using the all-mode cleanup prompt with targeted
    feedback. This preserves one generation pathway while keeping the public
    function available for future agent workflow changes.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}. Must be one of {MODES}")

    return run_cleanup(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
        mode=mode,
        existing_prompts=existing_prompts,
    )
