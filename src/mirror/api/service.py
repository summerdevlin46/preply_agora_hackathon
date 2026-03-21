import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from mirror.api.config_store import (
    get_chat_default_instructions,
    get_chat_instructions_by_id,
)
from mirror.api.schemas import (
    ChatInstructionsResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    WorksheetParseResponse,
)
from mirror.ocr import parse_worksheet

_PARSE_FAILURE_PREFIXES = (
    "Unsupported file type:",
    "No readable text could be extracted",
    "OCR error:",
)

_GENERATION_FAILURE_PREFIXES = (
    "Invalid model backend configuration.",
    "Model backend '",
    "No exercise was generated.",
)


async def parse_uploaded_worksheet(file: UploadFile) -> WorksheetParseResponse:
    suffix = Path(file.filename or "worksheet").suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        temp_path = Path(handle.name)
        content = await file.read()
        handle.write(content)

    try:
        worksheet_text = parse_worksheet(str(temp_path))
    finally:
        temp_path.unlink(missing_ok=True)

    if worksheet_text.startswith(_PARSE_FAILURE_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=worksheet_text,
        )

    return WorksheetParseResponse(
        filename=file.filename or temp_path.name,
        worksheet_text=worksheet_text,
    )


def generate_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    learner_name = payload.learner_name.strip()
    topic = payload.topic.strip()
    worksheet_text = payload.worksheet_text.strip()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Topic is required.",
        )

    if not worksheet_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Worksheet text is required.",
        )

    try:
        from mirror.agents import run_exercise_workflow
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Exercise generation dependencies are unavailable. "
                "Install the LLM dependency group before calling this endpoint."
            ),
        ) from exc

    exercise = run_exercise_workflow(
        learner_name=learner_name,
        topic=topic,
        worksheet_text=worksheet_text,
    )

    if exercise.startswith(_GENERATION_FAILURE_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exercise,
        )

    return ExerciseGenerationResponse(
        learner_name=learner_name,
        topic=topic,
        exercise=exercise,
    )


def get_default_chat_instructions() -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_default_instructions(),
    )


def get_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_instructions_by_id(chat_id),
    )
