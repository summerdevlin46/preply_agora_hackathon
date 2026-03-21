from typing import Any, TypedDict


class ExerciseState(TypedDict, total=False):
    # Inputs
    learner_name: str
    topic: str
    teacher_notes: str
    worksheet_json: dict[str, Any]

    # Output — all four mode prompts
    avatar_prompts: dict[str, str]

    # Regeneration
    feedback: str
    mode: str                   # which mode is being regenerated
    existing_prompts: dict[str, str]
    retry_count: int            # TODO: RL reward signal

    # Control
    error: str
