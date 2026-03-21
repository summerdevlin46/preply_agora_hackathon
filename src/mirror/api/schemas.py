from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ChatInstructionsResponse(BaseModel):
    instructions: Optional[str]


class WorksheetParseResponse(BaseModel):
    filename: str
    worksheet_json: dict
    worksheet_text: str  # raw_text field from OCR JSON for backwards compat


class ExerciseGenerationRequest(BaseModel):
    learner_name: str = Field(default="", max_length=200)
    topic: str = Field(min_length=1, max_length=300)
    worksheet_json: dict = Field(default_factory=dict)
    assignment_type: str = Field(default="grammar")
    teacher_notes: str = Field(default="")

    # Regeneration fields
    feedback: str = Field(default="")
    retry_count: int = Field(default=0)

    # If provided, save the generated prompt under this chat session
    chat_id: Optional[str] = Field(default=None)


class ExerciseGenerationResponse(BaseModel):
    chat_id: Optional[str]
    learner_name: str
    topic: str
    assignment_type: str
    avatar_prompt: str
    title: str
    objective: str
    avatar_name: str
    avatar_emoji: str
    tasks: list[dict]
    tip: str
