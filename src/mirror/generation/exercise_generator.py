import os

from mirror.generation.excerpt_selector import select_reference_excerpt
from mirror.generation.prompt_builder import build_exercise_prompt


def generate_exercise(learner_name: str, topic: str, worksheet_text: str) -> str:
    if not worksheet_text.strip():
        return "Please upload a worksheet first."

    reference_excerpt = select_reference_excerpt(worksheet_text)

    if not os.getenv("OPENAI_API_KEY"):
        return build_exercise_prompt(
            learner_name=learner_name,
            topic=topic,
            reference_excerpt=reference_excerpt,
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        return f"Generation error: missing OpenAI dependency: {exc}"

    prompt = build_exercise_prompt(
        learner_name=learner_name,
        topic=topic,
        reference_excerpt=reference_excerpt,
    )

    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5",
            input=prompt,
        )
        return response.output_text
    except Exception as exc:
        return f"Generation error: {exc}"
