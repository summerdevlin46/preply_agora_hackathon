from mirror.agents.state import ExerciseState
from mirror.generation.excerpt_selector import select_reference_excerpt
from mirror.generation.prompt_builder import build_exercise_prompt
from mirror.generation.repair_prompt import build_repair_prompt
from mirror.generation.style_analyzer import analyze_style
from mirror.generation.verifier import verify_generated_exercise
from mirror.models import generate_with_backend


def select_excerpt_node(state: ExerciseState) -> ExerciseState:
    worksheet_text = state.get("worksheet_text", "").strip()
    if not worksheet_text:
        return {"error": "Please upload a worksheet first."}

    return {"reference_excerpt": select_reference_excerpt(worksheet_text)}


def analyze_style_node(state: ExerciseState) -> ExerciseState:
    worksheet_text = state.get("worksheet_text", "").strip()
    if not worksheet_text:
        return {"error": "Worksheet text is missing."}

    return {"style_summary": analyze_style(worksheet_text)}


def build_prompt_node(state: ExerciseState) -> ExerciseState:
    learner_name = state.get("learner_name", "").strip() or "the learner"
    topic = state.get("topic", "").strip()
    teacher_prompt = state.get("teacher_prompt", "").strip()
    reference_excerpt = state.get("reference_excerpt", "").strip()
    style_summary = state.get("style_summary", "").strip()

    if not topic:
        return {"error": "Please provide a topic."}

    prompt = build_exercise_prompt(
        learner_name=learner_name,
        topic=topic,
        teacher_prompt=teacher_prompt,
        reference_excerpt=reference_excerpt,
        style_summary=style_summary,
    )
    return {"prompt": prompt}


def generate_node(state: ExerciseState) -> ExerciseState:
    prompt = state.get("prompt", "").strip()
    if not prompt:
        return {"error": "Prompt generation failed."}

    output = generate_with_backend(prompt=prompt)
    return {"output": output}


def verify_node(state: ExerciseState) -> ExerciseState:
    topic = state.get("topic", "").strip()
    output = state.get("output", "").strip()

    error = verify_generated_exercise(topic=topic, generated_text=output)
    if error:
        return {"error": error}

    return {"error": ""}


def build_repair_prompt_node(state: ExerciseState) -> ExerciseState:
    original_prompt = state.get("prompt", "").strip()
    topic = state.get("topic", "").strip()
    teacher_prompt = state.get("teacher_prompt", "").strip()
    bad_output = state.get("output", "").strip()
    verification_error = state.get("error", "").strip()

    repair_prompt = build_repair_prompt(
        original_prompt=original_prompt,
        topic=topic,
        teacher_prompt=teacher_prompt,
        bad_output=bad_output,
        verification_error=verification_error,
    )

    return {
        "repair_prompt": repair_prompt,
        "error": "",
        "retry_count": state.get("retry_count", 0) + 1,
    }


def repair_generate_node(state: ExerciseState) -> ExerciseState:
    repair_prompt = state.get("repair_prompt", "").strip()
    if not repair_prompt:
        return {"error": "Repair prompt generation failed."}

    output = generate_with_backend(prompt=repair_prompt)
    return {"output": output}
