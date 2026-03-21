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

_PARSE_FAILURE_PREFIXES = (
    "Unsupported file type:",
    "No readable text could be extracted",
    "OCR error:",
)

# Avatar config matching the frontend ASSIGNMENT_TYPES
_AVATAR_CONFIG = {
    "speaking": {"name": "Sofia", "emoji": "🧑‍🍳"},
    "vocab":    {"name": "Max",   "emoji": "🎤"},
    "writing":  {"name": "Priya", "emoji": "📋"},
    "grammar":  {"name": "Leo",   "emoji": "🕵️"},
}

_TASKS = {
    "speaking": [
        {"icon": "💬", "label": "Opening Question",  "content": "The avatar opens with a question about what you are doing right now. Answer in full present continuous sentences."},
        {"icon": "🗣️", "label": "Describe a Process", "content": "Walk through a process step by step using present continuous."},
        {"icon": "💡", "label": "Follow-Up",          "content": "The avatar asks a broader opinion question. Errors will be woven into corrections."},
    ],
    "vocab": [
        {"icon": "👂", "label": "Listen & Respond",   "content": "The avatar describes each word aloud. Say it when you know it, or type it in the chat."},
        {"icon": "🗣️", "label": "Use It in a Sentence", "content": "After each correct answer, use the word in a full sentence."},
        {"icon": "🔁", "label": "Missed Words Recap", "content": "The avatar revisits any words you hesitated on at the end."},
    ],
    "writing": [
        {"icon": "✏️", "label": "Type What You Hear",     "content": "The avatar reads a sentence aloud. Type exactly what you hear into the chat."},
        {"icon": "🔊", "label": "Listen for Corrections", "content": "The avatar gives spoken feedback after each sentence."},
        {"icon": "📊", "label": "Error Pattern Summary",  "content": "After all sentences, the avatar summarises patterns in your errors."},
    ],
    "grammar": [
        {"icon": "👂", "label": "Does That Sound Right?", "content": "The avatar reads a sentence and asks if it sounds correct. Say yes or give the correction."},
        {"icon": "📖", "label": "Explain the Rule",       "content": "When you spot an error, the avatar asks you to explain why it is wrong."},
        {"icon": "🏆", "label": "Score & Summary",        "content": "After all sentences, the avatar gives your score and reviews rules you found tricky."},
    ],
}

_TIPS = {
    "speaking": "The avatar waits for your complete answer before speaking. Take your time.",
    "vocab":    "All clues are spoken — you can type a word in chat if unsure how to pronounce it.",
    "writing":  "Type exactly what you hear — don't edit as you go. Corrections come after.",
    "grammar":  "Listen to the full sentence before deciding if it sounds right.",
}


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
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
    worksheet_json = payload.worksheet_json or {}
    assignment_type = payload.assignment_type or "grammar"

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Topic is required.",
        )

    avatar_prompt, error = run_prompt_workflow(
        teacher_notes=payload.teacher_notes or topic,
        worksheet_json=worksheet_json,
        feedback=payload.feedback or "",
        retry_count=payload.retry_count or 0,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error,
        )

    # Persist to SQLite so Next.js can fetch via /api/chat/{chat_id}/instructions
    chat_id = payload.chat_id or str(uuid.uuid4())
    save_chat_instructions(chat_id=chat_id, anam_prompt=avatar_prompt)

    avatar = _AVATAR_CONFIG.get(assignment_type, _AVATAR_CONFIG["grammar"])
    title_topic = worksheet_json.get("topic", topic)

    return ExerciseGenerationResponse(
        chat_id=chat_id,
        learner_name=payload.learner_name,
        topic=topic,
        assignment_type=assignment_type,
        avatar_prompt=avatar_prompt,
        title=f"{assignment_type.title()} Session: {title_topic}",
        objective=(payload.teacher_notes or topic)[:160],
        avatar_name=avatar["name"],
        avatar_emoji=avatar["emoji"],
        tasks=_TASKS.get(assignment_type, _TASKS["grammar"]),
        tip=_TIPS.get(assignment_type, "Take your time and speak clearly."),
    )


def get_default_chat_instructions() -> ChatInstructionsResponse:
    return ChatInstructionsResponse(instructions=get_chat_default_instructions())


def get_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_instructions_by_id(chat_id)
    )
