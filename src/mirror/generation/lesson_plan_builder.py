from typing import TypedDict

from mirror.generation.prompt_builder import build_exercise_prompt
from mirror.generation.tutor_prompt_builder import build_tutor_prompt


class LessonPlan(TypedDict):
    tutor_prompt: str
    exercise_prompt: str


def build_lesson_plan(
    learner_name: str,
    topic: str,
    teacher_prompt: str,
    reference_excerpt: str,
    style_summary: str,
) -> LessonPlan:
    tutor_prompt = build_tutor_prompt(
        learner_name=learner_name,
        topic=topic,
        teacher_prompt=teacher_prompt,
        reference_excerpt=reference_excerpt,
        style_summary=style_summary,
    )

    exercise_prompt = build_exercise_prompt(
        learner_name=learner_name,
        topic=topic,
        teacher_prompt=teacher_prompt,
        reference_excerpt=reference_excerpt,
        style_summary=style_summary,
    )

    return {
        "tutor_prompt": tutor_prompt,
        "exercise_prompt": exercise_prompt,
    }
