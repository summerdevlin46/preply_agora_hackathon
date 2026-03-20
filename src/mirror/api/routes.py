from fastapi import APIRouter, File, UploadFile

from mirror.api.schemas import (
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    HealthResponse,
    WorksheetParseResponse,
)
from mirror.api.service import generate_exercise, parse_uploaded_worksheet

router = APIRouter(prefix="/api", tags=["mirror"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/worksheet/parse", response_model=WorksheetParseResponse)
async def parse_worksheet(file: UploadFile = File(...)) -> WorksheetParseResponse:
    return await parse_uploaded_worksheet(file)


@router.post("/exercises/generate", response_model=ExerciseGenerationResponse)
def create_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    return generate_exercise(payload)
