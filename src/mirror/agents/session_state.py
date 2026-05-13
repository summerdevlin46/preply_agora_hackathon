from typing import Any, TypedDict


class SessionState(TypedDict, total=False):
    # Inputs
    chat_id: str
    messages: list[Any]

    # Transcript
    transcript_lines: list[str]
    transcript: str
    skipped_empty_messages: int

    # Analyses
    homework_analysis: str
    recommendation_raw: dict[str, Any]

    # Control
    error: str
