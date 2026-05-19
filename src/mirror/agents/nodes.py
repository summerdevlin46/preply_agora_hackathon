import logging

from mirror.agents.state import ExerciseState
from mirror.generation.cleanup import run_cleanup, run_single_mode_regeneration

logger = logging.getLogger(__name__)


def cleanup_node(state: ExerciseState) -> ExerciseState:
    """
    Calls the cleanup generation service.

    Fresh generation creates all four avatar modes.
    Feedback regeneration updates only the selected mode when existing prompts exist.
    """
    teacher_notes = state.get("teacher_notes", "").strip()
    worksheet_json = state.get("worksheet_json") or {}
    feedback = state.get("feedback", "").strip() or None
    mode = state.get("mode", "").strip() or None
    existing_prompts = state.get("existing_prompts") or None

    if not worksheet_json:
        return {"error": "No worksheet uploaded. Please upload a worksheet first."}

    try:
        if feedback and mode and existing_prompts:
            avatar_prompts = run_single_mode_regeneration(
                teacher_notes=teacher_notes,
                worksheet_json=worksheet_json,
                mode=mode,
                feedback=feedback,
                existing_prompts=existing_prompts,
            )
        else:
            avatar_prompts = run_cleanup(
                teacher_notes=teacher_notes,
                worksheet_json=worksheet_json,
            )
    except Exception as exc:
        ##logger.error("Cleanup node failed: %s", exc)
        logger.warning("Cleanup node failed; workflow may use fallback: %s", exc)
        logger.debug("Cleanup node failure details", exc_info=True)
        return {"error": str(exc)}

    return {"avatar_prompts": avatar_prompts, "error": ""}
