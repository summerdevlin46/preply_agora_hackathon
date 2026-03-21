from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ChatInstructionsResponse(BaseModel):
    instructions: Optional[str]


class WorksheetParseResponse(BaseModel):
    filename: str
    worksheet_text: str


class ExerciseGenerationRequest(BaseModel):
    learner_name: str = Field(default="", max_length=200)
    topic: str = Field(min_length=1, max_length=300)
    worksheet_text: str = Field(min_length=1)


class ExerciseGenerationResponse(BaseModel):
    learner_name: str
    topic: str
    exercise: str
