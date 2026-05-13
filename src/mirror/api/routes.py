from fastapi import APIRouter, File, UploadFile

from mirror.api.schemas import (
    ChatInstructionsResponse,
    ChatSessionResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    HealthResponse,
    HomeworkCompletionRequest,
    HomeworkCompletionResponse,
    StudentAnalysisResponse,
    TeacherReportResponse,
    WorksheetParseResponse,
)
from mirror.api.service import (
    complete_homework,
    generate_exercise,
    get_chat_instructions,
    get_chat_session,
    get_default_chat_instructions,
    parse_uploaded_worksheet,
)

router = APIRouter(prefix="/api", tags=["mirror"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/chat/get-user-chat-instructions",
    response_model=ChatInstructionsResponse,
)
def read_default_chat_instructions() -> ChatInstructionsResponse:
    return get_default_chat_instructions()


@router.get(
    "/chat/get-report",
    response_model=TeacherReportResponse,
)
def read_chat_report(chat_id: str) -> TeacherReportResponse:
    from fastapi import HTTPException, status

    from mirror.api.config_store import get_teacher_report

    report = get_teacher_report(chat_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found. Session may not be complete yet.",
        )

    return TeacherReportResponse(
        chat_id=report["chat_id"],
        transcript=report.get("transcript", ""),
        homework_analysis=report.get("analysis", ""),
        student_analysis=StudentAnalysisResponse(
            confidence_score=report.get("confidence_score", 0.0),
            fluency_score=report.get("fluency_score", 0.0),
            raw_turns=report.get("raw_turns", []),
        ),
    )


@router.get(
    "/chat/{chat_id}/instructions",
    response_model=ChatInstructionsResponse,
)
def read_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return get_chat_instructions(chat_id)


@router.get(
    "/chat/{chat_id}/session",
    response_model=ChatSessionResponse,
)
def read_chat_session(chat_id: str) -> ChatSessionResponse:
    return get_chat_session(chat_id)


@router.post(
    "/chat/{chat_id}/complete",
    response_model=HomeworkCompletionResponse,
)
async def complete_chat_homework(
    chat_id: str,
    payload: HomeworkCompletionRequest,
) -> HomeworkCompletionResponse:
    return await complete_homework(chat_id, payload)

@router.post("/worksheet/parse", response_model=WorksheetParseResponse)
async def parse_worksheet(file: UploadFile = File(...)) -> WorksheetParseResponse:
    return await parse_uploaded_worksheet(file)


@router.post("/exercises/generate", response_model=ExerciseGenerationResponse)
def create_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    return generate_exercise(payload)
