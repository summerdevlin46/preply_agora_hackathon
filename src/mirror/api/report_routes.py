import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from mirror.api.schemas import TeacherRecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["report"])


def _format_analysis(
    *,
    error_summary: str,
    strengths: str,
    areas_to_improve: str,
    suggested_next_topic: str,
) -> str:
    return (
        "Error summary:\n"
        f"{error_summary or 'No specific errors identified.'}\n\n"
        "Strengths:\n"
        f"{strengths or 'No specific strengths identified.'}\n\n"
        "Areas to improve:\n"
        f"{areas_to_improve or 'No specific areas identified.'}\n\n"
        "Suggested next topic:\n"
        f"{suggested_next_topic or 'No suggestion available.'}"
    )


@router.post("/analyze", response_model=TeacherRecommendationResponse)
@router.post("/analyse", response_model=TeacherRecommendationResponse)
async def analyze_session(
    chat_id: str = Form(...),
    transcript: str = Form(default=""),
    wav_file: UploadFile | None = File(default=None),
):
    """
    Generate teacher-facing recommendations from the session transcript.

    Audio biomarker analysis is currently disabled.
    wav_file is accepted for API compatibility and ignored for now.
    """
    from mirror.api.config_store import get_teacher_report, save_session_analysis
    from mirror.analysis.recommendation_service import analyze_session as run_analysis

    try:
        report = await run_analysis(
            chat_id=chat_id,
            transcript=transcript,
        )
    except Exception as exc:
        logger.error("Recommendation analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Recommendation analysis failed: {exc}",
        ) from exc

    analysis = _format_analysis(
        error_summary=report.error_summary,
        strengths=report.strengths,
        areas_to_improve=report.areas_to_improve,
        suggested_next_topic=report.suggested_next_topic,
    )

    # Keep existing storage shape for compatibility.
    # No biomarker provider is active, so scores are neutral placeholders.
    save_session_analysis(
        chat_id=chat_id,
        confidence_score=0.0,
        fluency_score=0.0,
        raw_turns=[report.raw_recommendations],
    )

    merged = get_teacher_report(chat_id) or {}

    return TeacherRecommendationResponse(
        chat_id=chat_id,
        confidence_score=0.0,
        fluency_score=0.0,
        transcript=merged.get("transcript", transcript),
        analysis=merged.get("analysis", analysis),
    )


@router.get("/{chat_id}/teacher", response_model=TeacherRecommendationResponse)
def get_teacher_report_endpoint(chat_id: str):
    from mirror.api.config_store import get_teacher_report

    report = get_teacher_report(chat_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found. Session may not be complete yet.",
        )

    return TeacherRecommendationResponse(
        chat_id=report["chat_id"],
        confidence_score=report.get("confidence_score", 0.0),
        fluency_score=report.get("fluency_score", 0.0),
        transcript=report.get("transcript", ""),
        analysis=report.get("analysis", ""),
    )
