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


class ChatSessionResponse(BaseModel):
    instructions: Optional[str]
    tasks: list[TaskItem] = Field(default_factory=list)
    tip: str = Field(default="")


class StudentAnalysisResponse(BaseModel):
    confidence_score: float = Field(default=0.0)
    fluency_score: float = Field(default=0.0)
    raw_turns: list[dict] = Field(default_factory=list)


class TeacherRecommendationResponse(BaseModel):
    chat_id: str
    confidence_score: float = Field(default=0.0)
    fluency_score: float = Field(default=0.0)
    transcript: str = Field(default="")
    analysis: str = Field(default="")

class TeacherReportResponse(BaseModel):
    chat_id: str
    transcript: str = Field(default="")
    homework_analysis: str = Field(default="")
    student_analysis: StudentAnalysisResponse


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
    used_fallback: bool = False
    warnings: list[str] = Field(default_factory=list)

class HomeworkTranscriptMessage(BaseModel):
    role: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    interrupted: bool = False


class HomeworkCompletionRequest(BaseModel):
    messages: list[HomeworkTranscriptMessage] = Field(min_length=1)


class HomeworkCompletionResponse(BaseModel):
    analysis: str
