"""
mirror/agents/exercise_workflow.py

Single-node workflow: cleanup → END
Returns all four avatar prompts in one shot.
"""
import logging

from langgraph.graph import END, START, StateGraph

from mirror.agents.nodes import cleanup_node
from mirror.agents.state import ExerciseState

logger = logging.getLogger(__name__)


def build_workflow():
    graph = StateGraph(ExerciseState)
    graph.add_node("cleanup", cleanup_node)
    graph.add_edge(START, "cleanup")
    graph.add_edge("cleanup", END)
    return graph.compile()


_WORKFLOW = build_workflow()


def run_prompt_workflow(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str = "",
    mode: str = "",
    existing_prompts: dict | None = None,
    retry_count: int = 0,
) -> tuple[dict[str, str], str]:
    """
    Returns (avatar_prompts, error).

    For fresh generation: pass teacher_notes + worksheet_json.
    For single-mode regeneration: also pass feedback, mode, existing_prompts.
    retry_count is tracked for future RL signal.

    TODO: log (mode, feedback, retry_count) pairs for bandit training.
    """
    result = _WORKFLOW.invoke(
        {
            "teacher_notes": teacher_notes,
            "worksheet_json": worksheet_json,
            "feedback": feedback,
            "mode": mode,
            "existing_prompts": existing_prompts or {},
            "retry_count": retry_count,
            "error": "",
        }
    )

    error = result.get("error", "")
    prompts = result.get("avatar_prompts", {})

    return prompts, error
