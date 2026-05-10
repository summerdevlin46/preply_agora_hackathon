"""
mirror/agents/nodes.py
"""
import logging

from mirror.agents.state import ExerciseState
from mirror.generation.cleanup import run_cleanup

logger = logging.getLogger(__name__)


def cleanup_node(state: ExerciseState) -> ExerciseState:
    """
    Calls the cleanup model to generate all four narrative avatar prompts.
    Handles both fresh generation and single-mode regeneration with feedback.
    """
    teacher_notes = state.get("teacher_notes", "").strip()
    worksheet_json = state.get("worksheet_json") or {}
    feedback = state.get("feedback", "").strip() or None
    mode = state.get("mode", "").strip() or None
    existing_prompts = state.get("existing_prompts") or None

    if not worksheet_json:
        return {"error": "No worksheet uploaded. Please upload a worksheet first."}

    try:
        avatar_prompts = run_cleanup(
            teacher_notes=teacher_notes,
            worksheet_json=worksheet_json,
            feedback=feedback,
            mode=mode,
            existing_prompts=existing_prompts,
        )
    except Exception as exc:
        logger.error("Cleanup node failed: %s", exc)
        return {"error": str(exc)}

    return {"avatar_prompts": avatar_prompts, "error": ""}
