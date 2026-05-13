import logging

from langgraph.graph import END, START, StateGraph

from mirror.agents.session_nodes import (
    build_transcript_node,
    homework_analysis_node,
    persist_session_report_node,
    recommendation_analysis_node,
)
from mirror.agents.session_state import SessionState

logger = logging.getLogger(__name__)


def _route_after_transcript(state: SessionState) -> str:
    """
    Stop the workflow early when transcript validation fails.

    This makes the graph behavior explicit instead of relying on later nodes
    silently skipping work when state["error"] exists.
    """
    if state.get("error"):
        return "error"

    return "ok"


def build_session_workflow():
    graph = StateGraph(SessionState)

    graph.add_node("build_transcript", build_transcript_node)
    graph.add_node("homework_analysis", homework_analysis_node)
    graph.add_node("recommendation_analysis", recommendation_analysis_node)
    graph.add_node("persist_report", persist_session_report_node)

    graph.add_edge(START, "build_transcript")

    graph.add_conditional_edges(
        "build_transcript",
        _route_after_transcript,
        {
            "error": END,
            "ok": "homework_analysis",
        },
    )

    graph.add_edge("homework_analysis", "recommendation_analysis")
    graph.add_edge("recommendation_analysis", "persist_report")
    graph.add_edge("persist_report", END)

    return graph.compile()


_SESSION_WORKFLOW = build_session_workflow()


async def run_session_workflow(
    *,
    chat_id: str,
    messages: list,
) -> SessionState:
    result = await _SESSION_WORKFLOW.ainvoke(
        {
            "chat_id": chat_id,
            "messages": messages,
            "error": "",
        }
    )

    return result
