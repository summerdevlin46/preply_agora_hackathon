import logging
from typing import Any

from mirror.agents.session_state import SessionState
from mirror.api.config_store import save_homework_wrap, save_session_analysis

logger = logging.getLogger(__name__)


_HOMEWORK_ANALYSIS_PROMPT = """You are writing a brief teacher-facing post-homework review.

Use the transcript below to identify concrete strengths and struggles.
Be specific and cite the transcript by line number when relevant.
Do not infer pronunciation, confidence, emotion, or audio quality unless the transcript explicitly contains that information.
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
    learner_turns = sum(1 for line in transcript_lines if ". USER:" in line)
    persona_turns = sum(1 for line in transcript_lines if ". PERSONA:" in line)

    return "\n".join(
        [
            (
                "Overall outcome: The session transcript was saved, but the "
                "automatic model-based homework summary was unavailable."
            ),
            (
                "Strengths: Transcript captured "
                f"{message_count} turns ({learner_turns} learner, "
                f"{persona_turns} tutor)."
            ),
            (
                "- Struggles: Automatic homework summary fallback was used because "
                f"{failure_reason}."
            ),
            (
                "- Struggles: Review the saved transcript manually for exact "
                "error patterns and correction quality."
            ),
            (
                "Recommended follow-up: Review the transcript and use the recommendation "
                "section for the next language focus."
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


def _message_attr(message: Any, name: str, default: Any = None) -> Any:
    if isinstance(message, dict):
        return message.get(name, default)

    return getattr(message, name, default)


def build_transcript_node(state: SessionState) -> SessionState:
    chat_id = state.get("chat_id", "").strip()
    messages = state.get("messages", [])

    logger.info(
        "session workflow building transcript for chat_id=%s with %s messages",
        chat_id or "<empty>",
        len(messages),
    )

    if not chat_id:
        return {"error": "Chat id is required."}

    transcript_lines: list[str] = []
    skipped_empty_messages = 0

    for index, message in enumerate(messages, start=1):
        role = str(_message_attr(message, "role", "")).strip()
        content = str(_message_attr(message, "content", "")).strip()
        interrupted = bool(_message_attr(message, "interrupted", False))

        if not content:
            skipped_empty_messages += 1
            continue

        interruption_suffix = " [interrupted]" if interrupted else ""
        transcript_lines.append(
            f"{index}. {role.upper()}: {content}{interruption_suffix}"
        )

    if not transcript_lines:
        return {
            "chat_id": chat_id,
            "skipped_empty_messages": skipped_empty_messages,
            "error": "Transcript messages are required.",
        }

    transcript = "\n".join(transcript_lines)

    return {
        "chat_id": chat_id,
        "transcript_lines": transcript_lines,
        "transcript": transcript,
        "skipped_empty_messages": skipped_empty_messages,
        "error": "",
    }


def homework_analysis_node(state: SessionState) -> SessionState:
    error = state.get("error", "")
    if error:
        return {}

    chat_id = state.get("chat_id", "")
    transcript = state.get("transcript", "")
    transcript_lines = state.get("transcript_lines", [])

    logger.info(
        "session workflow generating homework analysis for chat_id=%s transcript_chars=%s",
        chat_id,
        len(transcript),
    )

    try:
        analysis = _generate_homework_analysis(transcript)
        logger.info(
            "session workflow generated homework analysis for chat_id=%s analysis_chars=%s",
            chat_id,
            len(analysis),
        )
    except Exception as exc:
        logger.warning(
                "session workflow homework analysis failed for chat_id=%s; using fallback: %s",
                chat_id,
                exc,
        )
        logger.debug("Homework analysis failure details", exc_info=True)
        analysis = _build_fallback_homework_analysis(
            transcript_lines=transcript_lines,
            failure_reason=str(exc),
        )

    return {"homework_analysis": analysis}


async def recommendation_analysis_node(state: SessionState) -> SessionState:
    error = state.get("error", "")
    if error:
        return {}

    chat_id = state.get("chat_id", "")
    transcript = state.get("transcript", "")

    logger.info("session workflow generating recommendations for chat_id=%s", chat_id)

    try:
        from mirror.analysis.recommendation_service import analyze_session

        report = await analyze_session(
            chat_id=chat_id,
            transcript=transcript,
        )
        return {"recommendation_raw": report.raw_recommendations}
    except Exception as exc:
        logger.warning(
                "session workflow recommendation analysis failed for chat_id=%s: %s",
                chat_id,
                exc,
        )
        logger.debug("Recommendation analysis failure details", exc_info=True)
        return {
            "recommendation_raw": {
                "warnings": [
                    "Recommendation analysis failed during session workflow."
                ],
                "fallback_reason": str(exc),
            }
        }


def persist_session_report_node(state: SessionState) -> SessionState:
    error = state.get("error", "")
    if error:
        return {}

    chat_id = state.get("chat_id", "")
    transcript = state.get("transcript", "")
    homework_analysis = state.get("homework_analysis", "")
    recommendation_raw = state.get("recommendation_raw", {})

    was_updated = save_homework_wrap(
        chat_id=chat_id,
        transcript=transcript,
        analysis=homework_analysis,
    )

    if not was_updated:
        logger.error(
            "session workflow could not persist homework wrap because chat config was missing for chat_id=%s",
            chat_id,
        )
        return {
            "error": f"Chat config entry not found for id '{chat_id}'.",
        }

    save_session_analysis(
        chat_id=chat_id,
        confidence_score=0.0,
        fluency_score=0.0,
        raw_turns=[recommendation_raw] if recommendation_raw else [],
    )

    logger.info("session workflow persisted report for chat_id=%s", chat_id)

    return {}
