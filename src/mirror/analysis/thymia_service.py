"""
mirror/analysis/thymia_service.py

Post-session audio analysis via Thymia Helios (confidence + fluency)
combined with GPT-4o teacher report generation.
"""
import asyncio
import json
import logging
from dataclasses import dataclass

import websockets

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


async def _connect_sentinel(sentinel: SentinelClient) -> None:
    """
    Work around a protocol bug in thymia-sentinel 1.1.0.

    The packaged client sends the initial config without `type="CONFIG"`,
    which causes the server to reject the next AUDIO_HEADER frame.
    """
    if not sentinel.api_key:
        raise ValueError(
            "THYMIA_API_KEY environment variable or api_key parameter required"
        )

    sentinel._websocket = await websockets.connect(sentinel.server_url, max_size=None)

    progress_enabled = len(sentinel._progress_handlers) > 0
    config = {
        "type": "CONFIG",
        "api_key": sentinel.api_key,
        "language": sentinel.language,
        "biomarkers": sentinel.biomarkers,
        "policies": sentinel.policies,
        "audio_config": {
            "sample_rate": sentinel.sample_rate,
            "format": "pcm16",
            "channels": 1,
        },
        "progress_updates": {
            "enabled": progress_enabled,
            "interval_seconds": sentinel.progress_updates_frequency,
        },
    }
    if sentinel.user_label is not None:
        config["user_label"] = sentinel.user_label
    if sentinel.date_of_birth is not None:
        config["date_of_birth"] = sentinel.date_of_birth
    if sentinel.birth_sex is not None:
        config["birth_sex"] = sentinel.birth_sex
    if sentinel.custom_policies is not None:
        config["custom_policies"] = sentinel.custom_policies

    await sentinel._websocket.send(json.dumps(config))
    sentinel._receive_task = asyncio.create_task(sentinel._receive_server_events())
    sentinel._connected = True


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
    await _connect_sentinel(sentinel)

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


async def _generate_teacher_report(
    transcript: str,
    helios: HeliosResult,
) -> dict:
    from mirror.models.bedrock_backend import generate_text_async

    prompt = _TEACHER_REPORT_PROMPT.format(
        confidence=helios.confidence_score,
        fluency=helios.fluency_score,
        transcript=transcript.strip() or "No transcript available.",
    )

    raw = (
        await generate_text_async(
            system_prompt="You are an expert EFL/ESL language coach generating a teacher report.",
            user_message=prompt,
            max_tokens=600,
        )
    ).strip()

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
