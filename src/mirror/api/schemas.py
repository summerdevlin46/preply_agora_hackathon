from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ChatInstructionsResponse(BaseModel):
    instructions: Optional[str]


class WorksheetParseResponse(BaseModel):
    filename: str
    worksheet_json: dict
    worksheet_text: str


class TaskItem(BaseModel):
    title: str
    description: str


class ExerciseGenerationRequest(BaseModel):
    learner_name: str = Field(default="", max_length=200)
    topic: str = Field(min_length=1, max_length=300)
    worksheet_json: dict = Field(default_factory=dict)
    teacher_notes: str = Field(default="")
    feedback: str = Field(default="")
    mode: str = Field(default="")
    existing_prompts: dict = Field(default_factory=dict)
    retry_count: int = Field(default=0)
    chat_id: Optional[str] = Field(default=None)


class ExerciseGenerationResponse(BaseModel):
    chat_ids: dict[str, str]
    learner_name: str
    topic: str
    avatar_prompts: dict[str, str]
    tasks: dict[str, list[TaskItem]]
