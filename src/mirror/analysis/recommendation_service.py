import asyncio
import json
import logging
from dataclasses import dataclass

from mirror.models.factory import generate_with_backend

from mirror.generation.prompt_loader import load_prompt_spec

logger = logging.getLogger(__name__)
RECOMMENDATION_PROMPT_SPEC = load_prompt_spec("recommendation_report")


def _build_prompt(transcript: str) -> str:
    return RECOMMENDATION_PROMPT_SPEC.content.replace(
        "{transcript}",
        transcript.strip() or "No transcript available.",
    )


@dataclass
class RecommendationReport:
    chat_id: str
    transcript: str
    error_summary: str
    strengths: str
    areas_to_improve: str
    suggested_next_topic: str
    raw_recommendations: dict



def _strip_json_fences(raw: str) -> str:
    text = raw.strip()

    if not text.startswith("```"):
        return text

    parts = text.split("```")
    if len(parts) < 2:
        return text

    fenced = parts[1].strip()
    if fenced.lower().startswith("json"):
        fenced = fenced[4:].strip()

    return fenced

def _normalize_report_key(key: str) -> str:
    normalized = key.strip().lower().replace(" ", "_")

    aliases = {
        "error_summary": "error_summary",
        "errors": "error_summary",
        "strengths": "strengths",
        "areas_to_improve": "areas_to_improve",
        "area_to_improve": "areas_to_improve",
        "suggested_next_topic": "suggested_next_topic",
        "next_topic": "suggested_next_topic",
    }

    return aliases.get(normalized, normalized)


def _parse_loose_report(raw: str) -> dict:
    """
    Fallback for weak/local models that return label-style text instead of JSON.

    Example:
      Error_summary: "I never eats breakfast."
      Strengths: "..."
    """
    parsed: dict[str, str] = {}

    for line in raw.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        normalized_key = _normalize_report_key(key)

        if normalized_key not in {
            "error_summary",
            "strengths",
            "areas_to_improve",
            "suggested_next_topic",
        }:
            continue

        parsed[normalized_key] = value.strip().strip('"').strip("'")

    if not parsed:
        raise RuntimeError("Recommendation generation failed: invalid JSON.")

    return {
        "error_summary": parsed.get("error_summary", ""),
        "strengths": parsed.get("strengths", ""),
        "areas_to_improve": parsed.get("areas_to_improve", ""),
        "suggested_next_topic": parsed.get("suggested_next_topic", ""),
    }


def _parse_json(raw: str) -> dict:
    text = _strip_json_fences(raw)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Recommendation model returned non-JSON output; trying loose parser.")
        return _parse_loose_report(raw)

    if not isinstance(parsed, dict):
        raise RuntimeError("Recommendation generation failed: expected JSON object.")

    return parsed

async def analyze_session(
    chat_id: str,
    transcript: str = "",
) -> RecommendationReport:
    logger.info("Starting recommendation analysis for chat_id=%s", chat_id)
    logger.info(
        "Using recommendation prompt name=%s version=%s sha=%s",
        RECOMMENDATION_PROMPT_SPEC.name,
        RECOMMENDATION_PROMPT_SPEC.version,
        RECOMMENDATION_PROMPT_SPEC.sha256[:12],
    )

    prompt = _build_prompt(transcript)

    raw = await asyncio.to_thread(
        generate_with_backend,
        prompt,
        task="report",
        system_prompt="You are an expert EFL/ESL language coach generating teacher recommendations.",
    )

    parsed = _parse_json(raw)

    report = RecommendationReport(
        chat_id=chat_id,
        transcript=transcript,
        error_summary=str(parsed.get("error_summary", "")),
        strengths=str(parsed.get("strengths", "")),
        areas_to_improve=str(parsed.get("areas_to_improve", "")),
        suggested_next_topic=str(parsed.get("suggested_next_topic", "")),
        raw_recommendations=parsed,
    )

    logger.info("Recommendation analysis complete for chat_id=%s", chat_id)
    return report