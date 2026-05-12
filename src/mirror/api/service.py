import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from mirror.api.config_store import (
    get_chat_default_instructions,
    get_chat_instructions_by_id,
    get_chat_session_by_id,
    save_chat_instructions,
    save_homework_wrap,
)
from mirror.generation.demo_fallback import (
    demo_fallback_warning,
    is_demo_fallback_enabled,
    load_demo_fallback,
)
from mirror.api.schemas import (
    ChatInstructionsResponse,
    ChatSessionResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    HomeworkCompletionRequest,
    HomeworkCompletionResponse,
    WorksheetParseResponse,
)
from mirror.generation.cleanup import MODES

logger = logging.getLogger(__name__)
#TODO: Things are hardcoded as a backup. Need hardcoded mode maybe?
#idk...


_HOMEWORK_ANALYSIS_PROMPT = """You are writing a brief teacher-facing post-homework review.

Use the transcript below to identify concrete strengths and struggles.
Be specific and cite the transcript by line number when relevant.
If a student struggles with pronunciation or proper nouns, mention the exact line and quote the relevant excerpt.
Keep the output concise and directly usable by a teacher.

Return plain text with:
1. Overall outcome: 1-2 sentences.
2. Strengths: short sentence.
3. Struggles: 2-4 bullet-style lines beginning with "- ".
4. Recommended follow-up: 1 short sentence.

Transcript:
{transcript}
"""


def _build_fallback_homework_analysis(
    transcript_lines: list[str],
    failure_reason: str,
) -> str:
    message_count = len(transcript_lines)
    learner_turns = sum(
        1 for line in transcript_lines if ". USER:" in line
    )
    persona_turns = sum(
        1 for line in transcript_lines if ". PERSONA:" in line
    )

    return "\n".join(
        [
            (
                "Overall outcome: The session transcript was saved, but the "
                "automatic model-based analysis was unavailable."
            ),
            (
                "Strengths: Transcript captured "
                f"{message_count} turns ({learner_turns} learner, "
                f"{persona_turns} tutor)."
            ),
            (
                "- Struggles: Automatic analysis fallback was used because "
                f"{failure_reason}."
            ),
            (
                "- Struggles: Review the saved transcript manually for exact "
                "error patterns and correction quality."
            ),
            (
                "Recommended follow-up: Re-run homework analysis after "
                "restoring OpenAI access if you need a teacher-facing summary."
            ),
        ]
    )

def _looks_like_bad_homework_analysis(analysis: str) -> bool:
    normalized = analysis.strip().lower()

    if not normalized:
        return True

    bad_markers = [
        "1. overall outcome: 1-2 sentences",
        "2. strengths: short sentence",
        "3. struggles: 2-4 bullet-style lines",
        "transcript:",
    ]

    return any(marker in normalized for marker in bad_markers)

def _generate_homework_analysis(transcript: str) -> str:
    from mirror.models.factory import generate_with_backend

    analysis = generate_with_backend(
        prompt=_HOMEWORK_ANALYSIS_PROMPT.format(transcript=transcript),
        task="report",
        system_prompt=(
            "You are writing a brief teacher-facing post-homework review. "
            "Be specific, cite the transcript by line number, and keep output concise."
        ),
    ).strip()


    if _looks_like_bad_homework_analysis(analysis):
        raise RuntimeError("homework analysis model returned unusable prompt echo")

    return analysis

# Avatar config matching the frontend ASSIGNMENT_TYPES
_AVATAR_CONFIG = {
    "speaking": {"name": "Sofia", "emoji": "🧑‍🍳"},
    "vocab":    {"name": "Max",   "emoji": "🎤"},
    "writing":  {"name": "Priya", "emoji": "📋"},
    "grammar":  {"name": "Leo",   "emoji": "🕵️"},
}

_TIPS = {
    "speaking": "The avatar waits for your complete answer before speaking. Take your time.",
    "vocab":    "All clues are spoken — you can type a word in chat if unsure how to pronounce it.",
    "writing":  "Type exactly what you hear — don't edit as you go. Corrections come after.",
    "grammar":  "Listen to the full sentence before deciding if it sounds right.",
}

_MODE_TIPS = {
    "avatar_conversation": _TIPS["speaking"],
    "vocabulary_challenge": _TIPS["vocab"],
    "read_aloud_review": _TIPS["writing"],
    "error_detective": _TIPS["grammar"],
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
    using_fallback = False
    warnings: list[str] = []
    try:
        result, error = run_prompt_workflow(
            teacher_notes=payload.teacher_notes or topic,
            worksheet_json=payload.worksheet_json or {},
            feedback=payload.feedback or "",
            mode=payload.mode or "",
            existing_prompts=payload.existing_prompts or {},
            retry_count=payload.retry_count or 0,
        )
    except Exception as exc:
        logger.warning("Exercise generation failed: %s", exc)
        result, error = {}, str(exc)

    if error:
        if not is_demo_fallback_enabled():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Exercise generation failed and demo fallback is disabled. "
                    f"Original error: {error}"
                ),
            )

        logger.warning("Workflow returned error; using demo fallback: %s", error)
        using_fallback = True
        warnings.append(demo_fallback_warning(error))
        result = load_demo_fallback()

    # Extract tasks before building avatar_prompts so they don't bleed in
    tasks = result.get("tasks", {})
    avatar_prompts = {
        mode: str(result.get(mode, "")).strip()
        for mode in MODES
        if str(result.get(mode, "")).strip()
    }

    if not avatar_prompts:
        if not is_demo_fallback_enabled():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Exercise generation returned no avatar prompts.",
            )

        using_fallback = True
        warnings.append(
            "Exercise generation returned no avatar prompts. Serving demo fallback content."
        )
        result = load_demo_fallback()
        tasks = result.get("tasks", {})
        avatar_prompts = {
            mode: str(result.get(mode, "")).strip()
            for mode in MODES
            if str(result.get(mode, "")).strip()
        }

    if using_fallback:
        logger.info("Serving demo fallback prompts for topic=%s", topic)

    # Save one chat_id per mode to SQLite
    # Frontend navigates to /chat/{chat_id} to launch Anam for that mode
    chat_ids = {}
    base_id = payload.chat_id or str(uuid.uuid4())
    for mode in MODES:
        prompt = avatar_prompts.get(mode, "")
        if not prompt:
            continue
        chat_id = f"{base_id}-{mode}"
        save_chat_instructions(
            chat_id=chat_id,
            anam_prompt=prompt,
            tasks=tasks.get(mode, []),
            tip=_MODE_TIPS.get(mode, ""),
        )
        chat_ids[mode] = chat_id

    return ExerciseGenerationResponse(
        chat_ids=chat_ids,
        learner_name=payload.learner_name,
        topic=topic,
        avatar_prompts=avatar_prompts,
        tasks=tasks,
        used_fallback=using_fallback,
        warnings=warnings,
    )


def get_default_chat_instructions() -> ChatInstructionsResponse:
    return ChatInstructionsResponse(instructions=get_chat_default_instructions())


def get_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_instructions_by_id(chat_id)
    )


def get_chat_session(chat_id: str) -> ChatSessionResponse:
    session = get_chat_session_by_id(chat_id)
    if session is None:
        return ChatSessionResponse(instructions=None)

    return ChatSessionResponse(**session)


def complete_homework(
    chat_id: str,
    payload: HomeworkCompletionRequest,
) -> HomeworkCompletionResponse:
    normalized_chat_id = chat_id.strip()
    total_messages = len(payload.messages)
    logger.info(
        "complete_homework started for chat_id=%s with %s incoming messages",
        normalized_chat_id or "<empty>",
        total_messages,
    )

    if not normalized_chat_id:
        logger.warning("complete_homework rejected request with empty chat_id")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chat id is required.",
        )

    transcript_lines: list[str] = []
    skipped_empty_messages = 0
    for index, message in enumerate(payload.messages, start=1):
        content = message.content.strip()
        if not content:
            skipped_empty_messages += 1
            continue

        interruption_suffix = " [interrupted]" if message.interrupted else ""
        transcript_lines.append(
            f"{index}. {message.role.upper()}: {content}{interruption_suffix}"
        )

    logger.info(
        (
            "complete_homework built transcript for chat_id=%s with %s lines "
            "(skipped_empty_messages=%s)"
        ),
        normalized_chat_id,
        len(transcript_lines),
        skipped_empty_messages,
    )

    if not transcript_lines:
        logger.warning(
            "complete_homework rejected chat_id=%s because transcript was empty after normalization",
            normalized_chat_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcript messages are required.",
        )

    transcript = "\n".join(transcript_lines)
    logger.info(
        "complete_homework requesting analysis for chat_id=%s (transcript_chars=%s)",
        normalized_chat_id,
        len(transcript),
    )

    try:
        analysis = _generate_homework_analysis(transcript)
        logger.info(
            "complete_homework generated analysis for chat_id=%s (analysis_chars=%s)",
            normalized_chat_id,
            len(analysis),
        )
    except Exception as exc:
        logger.exception(
            "complete_homework analysis generation failed for chat_id=%s; using fallback",
            normalized_chat_id,
        )
        analysis = _build_fallback_homework_analysis(
            transcript_lines=transcript_lines,
            failure_reason=str(exc),
        )
        logger.warning(
            "complete_homework fallback analysis created for chat_id=%s (analysis_chars=%s)",
            normalized_chat_id,
            len(analysis),
        )

    was_updated = save_homework_wrap(
        chat_id=normalized_chat_id,
        transcript=transcript,
        analysis=analysis,
    )
    if not was_updated:
        logger.error(
            "complete_homework could not persist results because chat config was missing for chat_id=%s",
            normalized_chat_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat config entry not found for id '{normalized_chat_id}'.",
        )

    logger.info(
        "complete_homework persisted transcript and analysis for chat_id=%s",
        normalized_chat_id,
    )
    return HomeworkCompletionResponse(analysis=analysis)
