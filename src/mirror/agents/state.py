from typing import TypedDict


class ExerciseState(TypedDict, total=False):
    learner_name: str
    topic: str
    teacher_prompt: str
    worksheet_text: str
    reference_excerpt: str
    style_summary: str
    prompt: str
    output: str
    error: str
    repair_prompt: str
    retry_count: int
