"""
mirror/api/report_routes.py

Add to src/app.py:
    from mirror.api.report_routes import router as report_router
    app.include_router(report_router)
"""
import logging
from pathlib import Path
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["report"])


class TeacherReportResponse(BaseModel):
    chat_id: str
    confidence_score: float
    fluency_score: float
    transcript: str
    analysis: str


@router.post("/analyze", response_model=TeacherReportResponse)
async def analyze_session(
    chat_id: str = Form(...),
    transcript: str = Form(default=""),
    wav_file: UploadFile = File(...),
):
    """
    Accepts WAV from Anam SDK.
    Runs Thymia Helios and saves scores to session_analysis table.
    Fires independently from complete_homework — both run after session ends.
    """
    from mirror.analysis.thymia_service import analyze_session as run_analysis
    from mirror.api.config_store import save_session_analysis, get_teacher_report

    suffix = Path(wav_file.filename or "session.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        content = await wav_file.read()
        tmp.write(content)

    try:
        report = await run_analysis(
            chat_id=chat_id,
            wav_path=str(tmp_path),
            transcript=transcript,
        )
    except Exception as exc:
        logger.error("Thymia analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Thymia analysis failed: {exc}",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    # Save Thymia scores to SQLite
    save_session_analysis(
        chat_id=chat_id,
        confidence_score=report.confidence_score,
        fluency_score=report.fluency_score,
        raw_turns=report.raw_turns,
    )

    # Merge with homework analysis if already saved by complete_homework
    merged = get_teacher_report(chat_id) or {}

    return TeacherReportResponse(
        chat_id=chat_id,
        confidence_score=report.confidence_score,
        fluency_score=report.fluency_score,
        transcript=merged.get("transcript", transcript),
        analysis=merged.get("analysis", "Analysis pending."),
    )


@router.get("/{chat_id}/teacher", response_model=TeacherReportResponse)
def get_teacher_report_endpoint(chat_id: str):
    """
    Merged teacher report — Thymia scores + GPT homework analysis.
    Both complete_homework and /analyze must have run for a complete report.
    """
    from mirror.api.config_store import get_teacher_report

    report = get_teacher_report(chat_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found. Session may not be complete yet.",
        )

    return TeacherReportResponse(
        chat_id=report["chat_id"],
        confidence_score=report["confidence_score"],
        fluency_score=report["fluency_score"],
        transcript=report["transcript"],
        analysis=report["analysis"],
    )
