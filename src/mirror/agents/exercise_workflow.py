from langgraph.graph import END, START, StateGraph

from mirror.agents.nodes import (
    analyze_style_node,
    build_prompt_node,
    build_repair_prompt_node,
    generate_node,
    repair_generate_node,
    select_excerpt_node,
    verify_node,
)
from mirror.agents.routers import generic_router, route_after_verify, start_router
from mirror.agents.state import ExerciseState


def build_workflow():
    graph = StateGraph(ExerciseState)

    graph.add_node("select_excerpt", select_excerpt_node)
    graph.add_node("analyze_style", analyze_style_node)
    graph.add_node("build_prompt", build_prompt_node)
    graph.add_node("generate", generate_node)
    graph.add_node("verify", verify_node)
    graph.add_node("build_repair_prompt", build_repair_prompt_node)
    graph.add_node("repair_generate", repair_generate_node)

    graph.add_conditional_edges(
        START,
        start_router,
        {"select_excerpt": "select_excerpt", "end": END},
    )
    graph.add_conditional_edges(
        "select_excerpt",
        generic_router("analyze_style"),
        {"analyze_style": "analyze_style", "end": END},
    )
    graph.add_conditional_edges(
        "analyze_style",
        generic_router("build_prompt"),
        {"build_prompt": "build_prompt", "end": END},
    )
    graph.add_conditional_edges(
        "build_prompt",
        generic_router("generate"),
        {"generate": "generate", "end": END},
    )
    graph.add_conditional_edges(
        "generate",
        generic_router("verify"),
        {"verify": "verify", "end": END},
    )
    graph.add_conditional_edges(
        "verify",
        route_after_verify,
        {"build_repair_prompt": "build_repair_prompt", "end": END},
    )
    graph.add_conditional_edges(
        "build_repair_prompt",
        generic_router("repair_generate"),
        {"repair_generate": "repair_generate", "end": END},
    )
    graph.add_conditional_edges(
        "repair_generate",
        generic_router("verify"),
        {"verify": "verify", "end": END},
    )

    return graph.compile()


_WORKFLOW = build_workflow()


def run_exercise_workflow(
    learner_name: str,
    topic: str,
    teacher_prompt: str,
    worksheet_text: str,
) -> str:
    result = _WORKFLOW.invoke(
        {
            "learner_name": learner_name,
            "topic": topic,
            "teacher_prompt": teacher_prompt,
            "worksheet_text": worksheet_text,
            "retry_count": 0,
            "error": "",
        }
    )

    if result.get("error"):
        return result["error"]

    return result.get("output", "No exercise was generated.")
