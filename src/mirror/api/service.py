import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from mirror.api.config_store import (
    get_chat_default_instructions,
    get_chat_instructions_by_id,
    save_chat_instructions,
)
from mirror.api.schemas import (
    ChatInstructionsResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    WorksheetParseResponse,
)
from mirror.generation.cleanup import MODES


async def parse_uploaded_worksheet(file: UploadFile) -> WorksheetParseResponse:
    from mirror.ocr.vision_parser import parse_worksheet_to_json

    suffix = Path(file.filename or "worksheet").suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        temp_path = Path(handle.name)
        content = await file.read()
        handle.write(content)

    try:
        worksheet_json = parse_worksheet_to_json(str(temp_path))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    finally:
        temp_path.unlink(missing_ok=True)

    return WorksheetParseResponse(
        filename=file.filename or temp_path.name,
        worksheet_json=worksheet_json,
        worksheet_text=worksheet_json.get("raw_text", ""),
    )


def generate_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    from mirror.agents.exercise_workflow import run_prompt_workflow

    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Topic is required.",
        )

    # result is the full dict: {mode: prompt, ..., tasks: {mode: [...]}}
    result, error = run_prompt_workflow(
        teacher_notes=payload.teacher_notes or topic,
        worksheet_json=payload.worksheet_json or {},
        feedback=payload.feedback or "",
        mode=payload.mode or "",
        existing_prompts=payload.existing_prompts or {},
        retry_count=payload.retry_count or 0,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=error)

    # Extract tasks before building avatar_prompts so they don't bleed in
    tasks = result.pop("tasks", {})
    avatar_prompts = {m: result[m] for m in MODES if m in result}

    # Save one chat_id per mode to SQLite
    # Frontend navigates to /chat/{chat_id} to launch Anam for that mode
    chat_ids = {}
    base_id = payload.chat_id or str(uuid.uuid4())
    for mode in MODES:
        prompt = avatar_prompts.get(mode, "")
        if not prompt:
            continue
        chat_id = f"{base_id}-{mode}"
        save_chat_instructions(chat_id=chat_id, anam_prompt=prompt)
        chat_ids[mode] = chat_id

    return ExerciseGenerationResponse(
        chat_ids=chat_ids,
        learner_name=payload.learner_name,
        topic=topic,
        avatar_prompts=avatar_prompts,
        tasks=tasks,
    )


def get_default_chat_instructions() -> ChatInstructionsResponse:
    return ChatInstructionsResponse(instructions=get_chat_default_instructions())


def get_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_instructions_by_id(chat_id)
    )
