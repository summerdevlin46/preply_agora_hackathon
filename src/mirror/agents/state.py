from typing import Any, TypedDict


class ExerciseState(TypedDict, total=False):
    # Inputs
    learner_name: str
    topic: str
    teacher_notes: str          # raw notes typed by teacher in UI
    worksheet_json: dict[str, Any]  # structured OCR output

    # Intermediate
    goal_block: str             # cleaned GOAL section
    context_block: str          # cleaned USEFUL CONTEXT section

    # Output
    avatar_system_prompt: str   # full assembled prompt for Anam

    # Regeneration
    feedback: str               # teacher's rejection reason
    retry_count: int            # TODO: feed into RL reward signal long-term

    # Control
    error: str
