"""
mirror/agents/exercise_workflow.py

Slim two-node workflow:
  cleanup → build_prompt → END
Regeneration is handled by re-invoking with feedback in state.
"""
import logging

from langgraph.graph import END, START, StateGraph

from mirror.agents.nodes import build_prompt_node, cleanup_node
from mirror.agents.state import ExerciseState

logger = logging.getLogger(__name__)


def _route(next_node: str):
    """Generic router — go to next_node or END on error."""
    def router(state: ExerciseState) -> str:
        if state.get("error"):
            logger.warning("Workflow ending early: %s", state["error"])
            return "end"
        return next_node
    return router


def build_workflow():
    graph = StateGraph(ExerciseState)

    graph.add_node("cleanup", cleanup_node)
    graph.add_node("build_prompt", build_prompt_node)

    graph.add_edge(START, "cleanup")
    graph.add_conditional_edges(
        "cleanup",
        _route("build_prompt"),
        {"build_prompt": "build_prompt", "end": END},
    )
    graph.add_edge("build_prompt", END)

    return graph.compile()


_WORKFLOW = build_workflow()


def run_prompt_workflow(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str = "",
    retry_count: int = 0,
) -> tuple[str, str]:
    """
    Returns (avatar_system_prompt, error).
    Pass feedback for regeneration — retry_count tracked for future RL signal.

    TODO: use retry_count as negative reward signal in bandit long-term.
    """
    result = _WORKFLOW.invoke(
        {
            "teacher_notes": teacher_notes,
            "worksheet_json": worksheet_json,
            "feedback": feedback,
            "retry_count": retry_count,
            "error": "",
        }
    )

    error = result.get("error", "")
    prompt = result.get("avatar_system_prompt", "")

    return prompt, error
