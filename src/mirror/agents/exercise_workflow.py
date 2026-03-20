from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from mirror.generation.excerpt_selector import select_reference_excerpt
from mirror.generation.prompt_builder import build_exercise_prompt
from mirror.generation.style_analyzer import analyze_style
from mirror.generation.exercise_generator import generate_exercise_text


class ExerciseState(TypedDict, total=False):
    learner_name: str
    topic: str
    worksheet_text: str
    reference_excerpt: str
    style_summary: str
    prompt: str
    output: str
    error: str


def select_excerpt_node(state: ExerciseState) -> ExerciseState:
    worksheet_text = state.get("worksheet_text", "").strip()
    if not worksheet_text:
        return {"error": "Please upload a worksheet first."}

    return {
        "reference_excerpt": select_reference_excerpt(worksheet_text)
    }


def analyze_style_node(state: ExerciseState) -> ExerciseState:
    worksheet_text = state.get("worksheet_text", "").strip()
    if not worksheet_text:
        return {"error": "Worksheet text is missing."}

    return {
        "style_summary": analyze_style(worksheet_text)
    }


def build_prompt_node(state: ExerciseState) -> ExerciseState:
    learner_name = state.get("learner_name", "").strip()
    topic = state.get("topic", "").strip()
    reference_excerpt = state.get("reference_excerpt", "").strip()
    style_summary = state.get("style_summary", "").strip()

    if not topic:
        return {"error": "Please provide a topic."}

    prompt = build_exercise_prompt(
        learner_name=learner_name or "the learner",
        topic=topic,
        reference_excerpt=reference_excerpt,
        style_summary=style_summary,
    )
    return {"prompt": prompt}


def generate_node(state: ExerciseState) -> ExerciseState:
    prompt = state.get("prompt", "").strip()
    if not prompt:
        return {"error": "Prompt generation failed."}

    output = generate_exercise_text(prompt)
    return {"output": output}


def route_after_validation(state: ExerciseState) -> str:
    if state.get("error"):
        return "end"
    return "select_excerpt"


def route_after_excerpt(state: ExerciseState) -> str:
    if state.get("error"):
        return "end"
    return "analyze_style"


def route_after_style(state: ExerciseState) -> str:
    if state.get("error"):
        return "end"
    return "build_prompt"


def route_after_prompt(state: ExerciseState) -> str:
    if state.get("error"):
        return "end"
    return "generate"


def build_workflow():
    graph = StateGraph(ExerciseState)

    graph.add_node("select_excerpt", select_excerpt_node)
    graph.add_node("analyze_style", analyze_style_node)
    graph.add_node("build_prompt", build_prompt_node)
    graph.add_node("generate", generate_node)

    graph.add_conditional_edges(
        START,
        route_after_validation,
        {
            "select_excerpt": "select_excerpt",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "select_excerpt",
        route_after_excerpt,
        {
            "analyze_style": "analyze_style",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "analyze_style",
        route_after_style,
        {
            "build_prompt": "build_prompt",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "build_prompt",
        route_after_prompt,
        {
            "generate": "generate",
            "end": END,
        },
    )
    graph.add_edge("generate", END)

    return graph.compile()


_WORKFLOW = build_workflow()


def run_exercise_workflow(learner_name: str, topic: str, worksheet_text: str) -> str:
    result = _WORKFLOW.invoke(
        {
            "learner_name": learner_name,
            "topic": topic,
            "worksheet_text": worksheet_text,
        }
    )

    if result.get("error"):
        return result["error"]

    return result.get("output", "No exercise was generated.")
