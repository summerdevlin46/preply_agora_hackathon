"""
mirror/analysis/thymia_service.py

Post-session audio analysis via Thymia Helios (confidence + fluency)
combined with GPT-4o teacher report generation.
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from thymia_sentinel import SentinelClient

logger = logging.getLogger(__name__)


@dataclass
class HeliosResult:
    confidence_score: float
    fluency_score: float
    raw_turns: list[dict]


@dataclass
class TeacherReport:
    chat_id: str
    confidence_score: float
    fluency_score: float
    transcript: str
    error_summary: str
    strengths: str
    areas_to_improve: str
    suggested_next_topic: str
    raw_turns: list[dict]


def _load_wav_pcm16(path: str) -> bytes:
    import wave
    with wave.open(path, "rb") as wf:
        if wf.getsampwidth() != 2:
            raise ValueError("WAV must be 16-bit PCM")
        if wf.getframerate() != 16000:
            raise ValueError("WAV must be 16kHz sample rate")
        if wf.getnchannels() != 1:
            raise ValueError("WAV must be mono")
        return wf.readframes(wf.getnframes())


async def _stream_to_helios(wav_path: str) -> HeliosResult:
    pcm_data = _load_wav_pcm16(wav_path)

    turns: list[dict] = []
    final_confidence = 0.0
    final_fluency = 0.0

    sentinel = SentinelClient(
        user_label="mirror-session-analysis",
        policies=[],
        biomarkers=["helios"],
        sample_rate=16000,
    )

    @sentinel.on_policy_result
    async def on_result(result):
        nonlocal final_confidence, final_fluency
        logger.info("Helios result: %s", result)
        turns.append(result)
        scores = result.get("scores", {})
        if "confidence" in scores:
            final_confidence = scores["confidence"]
        if "fluency" in scores:
            final_fluency = scores["fluency"]

    logger.info("Connecting to Thymia Sentinel...")
    await sentinel.connect()

    chunk_duration_ms = 100
    bytes_per_chunk = 2 * 16000 * chunk_duration_ms // 1000
    total_chunks = (len(pcm_data) + bytes_per_chunk - 1) // bytes_per_chunk
    logger.info("Streaming %d chunks to Helios", total_chunks)

    for i in range(total_chunks):
        start = i * bytes_per_chunk
        chunk = pcm_data[start : start + bytes_per_chunk]
        await sentinel.send_user_audio(chunk)
        await asyncio.sleep(chunk_duration_ms / 1000.0)

    logger.info("Waiting for final Helios results...")
    await asyncio.sleep(5)
    await sentinel.close()

    return HeliosResult(
        confidence_score=round(final_confidence, 3),
        fluency_score=round(final_fluency, 3),
        raw_turns=turns,
    )


_TEACHER_REPORT_PROMPT = """You are an expert EFL/ESL language coach reviewing a student's spoken grammar session.

You will receive confidence and fluency scores (0-1) from voice biomarker analysis and a transcript.

Generate a concise teacher report. Return valid JSON only, no preamble, no markdown fences.

Schema:
{{
  "error_summary": "specific grammar errors made with examples from transcript",
  "strengths": "what the student did well",
  "areas_to_improve": "specific patterns to practise with examples",
  "suggested_next_topic": "one concrete recommendation for next session"
}}

Confidence score: {confidence}
Fluency score: {fluency}

Transcript:
{transcript}
"""


def _extract_text(response) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    try:
        return "".join(
            block.text
            for item in response.output
            for block in item.content
            if block.type == "output_text"
        )
    except Exception:
        return str(response)


async def _generate_teacher_report(
    transcript: str,
    helios: HeliosResult,
) -> dict:
    from openai import AsyncOpenAI
    from mirror.config import get_env

    client = AsyncOpenAI(api_key=get_env("OPENAI_API_KEY"))

    prompt = _TEACHER_REPORT_PROMPT.format(
        confidence=helios.confidence_score,
        fluency=helios.fluency_score,
        transcript=transcript.strip() or "No transcript available.",
    )

    response = await client.responses.create(
        model="gpt-4o",
        input=prompt,
        max_output_tokens=600,
    )

    raw = _extract_text(response).strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Report model returned invalid JSON:\n%s", raw)
        raise RuntimeError("Report generation failed.") from exc


async def analyze_session(
    chat_id: str,
    wav_path: str,
    transcript: str = "",
) -> TeacherReport:
    """
    Full post-session analysis pipeline.

    Args:
        chat_id:    Session ID — used to save/retrieve the report
        wav_path:   Path to 16kHz mono PCM16 WAV from Anam SDK
        transcript: Optional transcript from Anam. GPT-4o uses biomarkers alone if empty.

    Returns:
        TeacherReport dataclass
    """
    logger.info("Starting session analysis for chat_id=%s", chat_id)

    helios = await _stream_to_helios(wav_path)
    logger.info(
        "Helios complete — confidence=%.3f fluency=%.3f turns=%d",
        helios.confidence_score, helios.fluency_score, len(helios.raw_turns),
    )

    gpt_report = await _generate_teacher_report(transcript=transcript, helios=helios)

    report = TeacherReport(
        chat_id=chat_id,
        confidence_score=helios.confidence_score,
        fluency_score=helios.fluency_score,
        transcript=transcript,
        error_summary=gpt_report.get("error_summary", ""),
        strengths=gpt_report.get("strengths", ""),
        areas_to_improve=gpt_report.get("areas_to_improve", ""),
        suggested_next_topic=gpt_report.get("suggested_next_topic", ""),
        raw_turns=helios.raw_turns,
    )

    logger.info("Analysis complete for chat_id=%s", chat_id)
    return report
