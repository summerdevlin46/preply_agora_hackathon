"""
mirror/agents/nodes.py

LangGraph nodes for the avatar prompt generation workflow.
"""
import logging

from mirror.agents.state import ExerciseState
from mirror.generation.cleanup import run_cleanup
from mirror.generation.prompt_builder import build_avatar_system_prompt

logger = logging.getLogger(__name__)


def cleanup_node(state: ExerciseState) -> ExerciseState:
    """
    Calls the cleanup model to turn raw teacher notes + worksheet JSON
    into structured GOAL and USEFUL CONTEXT blocks.
    Passes feedback if this is a regeneration.
    """
    teacher_notes = state.get("teacher_notes", "").strip()
    worksheet_json = state.get("worksheet_json") or {}
    feedback = state.get("feedback", "").strip() or None

    if not worksheet_json:
        return {"error": "No worksheet uploaded. Please upload a worksheet first."}

    try:
        goal_block, context_block = run_cleanup(
            teacher_notes=teacher_notes,
            worksheet_json=worksheet_json,
            feedback=feedback,
        )
    except RuntimeError as exc:
        logger.error("Cleanup node failed: %s", exc)
        return {"error": str(exc)}

    return {
        "goal_block": goal_block,
        "context_block": context_block,
        "error": "",
    }


def build_prompt_node(state: ExerciseState) -> ExerciseState:
    """
    Assembles the full avatar system prompt from static template
    and cleaned GOAL + USEFUL CONTEXT blocks.
    """
    goal_block = state.get("goal_block", "").strip()
    context_block = state.get("context_block", "").strip()

    if not goal_block or not context_block:
        return {"error": "Cleanup step did not produce valid blocks."}

    avatar_system_prompt = build_avatar_system_prompt(
        goal_block=goal_block,
        context_block=context_block,
    )

    return {
        "avatar_system_prompt": avatar_system_prompt,
        "error": "",
    }
