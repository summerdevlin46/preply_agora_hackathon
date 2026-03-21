from fastapi import APIRouter, File, UploadFile

from mirror.api.schemas import (
    ChatInstructionsResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    HealthResponse,
    WorksheetParseResponse,
)
from mirror.api.service import (
    generate_exercise,
    get_chat_instructions,
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
    "/chat/{chat_id}/instructions",
    response_model=ChatInstructionsResponse,
)
def read_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return get_chat_instructions(chat_id)


@router.post("/worksheet/parse", response_model=WorksheetParseResponse)
async def parse_worksheet(file: UploadFile = File(...)) -> WorksheetParseResponse:
    return await parse_uploaded_worksheet(file)


@router.post("/exercises/generate", response_model=ExerciseGenerationResponse)
def create_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    return generate_exercise(payload)
