import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from mirror.generation.prompt_loader import load_prompt_spec
from mirror.models.factory import generate_with_backend

logger = logging.getLogger(__name__)

RECOMMENDATION_PROMPT_SPEC = load_prompt_spec("recommendation_report")

REPORT_FIELDS = (
    "error_summary",
    "strengths",
    "areas_to_improve",
    "suggested_next_topic",
)

STUDENT_ROLES = {"student", "learner", "user"}
TEACHER_ROLES = {"teacher", "tutor", "assistant"}


@dataclass
class TranscriptSignals:
    student_turn_count: int
    teacher_turn_count: int
    learner_examples: list[str] = field(default_factory=list)
    teacher_corrections: list[str] = field(default_factory=list)
    possible_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RecommendationReport:
    chat_id: str
    transcript: str
    error_summary: str
    strengths: str
    areas_to_improve: str
    suggested_next_topic: str
    raw_recommendations: dict[str, Any]


def _iter_transcript_turns(transcript: str) -> list[tuple[str, str]]:
    """
    Extract role-labeled turns from either multiline or inline transcripts.

    Handles:
      Teacher: Hello
      Student: Hi

    And:
      Teacher: Hello Student: Hi
    """
    pattern = re.compile(
        r"\b(teacher|tutor|assistant|student|learner|user)\s*:\s*",
        flags=re.IGNORECASE,
    )

    matches = list(pattern.finditer(transcript))
    if not matches:
        return []

    turns: list[tuple[str, str]] = []

    for index, match in enumerate(matches):
        role = match.group(1).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(transcript)
        content = transcript[start:end].strip()

        if content:
            turns.append((role, f"{role.title()}: {content}"))

    return turns


def _extract_transcript_signals(transcript: str) -> TranscriptSignals:
    """
    Deterministic transcript analysis.

    This gives the recommendation system reliable evidence before asking the
    model to reason or write teacher-facing feedback.
    """
    student_turns: list[str] = []
    teacher_turns: list[str] = []
    teacher_corrections: list[str] = []
    possible_errors: list[str] = []
    warnings: list[str] = []

    for role, line in _iter_transcript_turns(transcript):
        lower = line.lower()

        if role in STUDENT_ROLES:
            student_turns.append(line)
        elif role in TEACHER_ROLES:
            teacher_turns.append(line)

        if role in TEACHER_ROLES and any(
            marker in lower
            for marker in ["say:", "correct:", "correction:", "try again", "good try"]
        ):
            teacher_corrections.append(line)

    joined_student_turns = " ".join(student_turns).lower()

    # Demo-useful grammar signal. This is not a full grammar checker.
    # It catches patterns like "she is bake" where present continuous likely needs -ing.
    be_base_verb_pattern = re.compile(
        r"\b(am|is|are)\s+"
        r"(bake|cook|mix|fry|boil|chop|grill|pour|whisk|eat|make|do|go|play|read|write)\b"
    )

    for match in be_base_verb_pattern.finditer(joined_student_turns):
        possible_errors.append(
            f"Possible present continuous form issue: '{match.group(0)}' may need a verb-ing form."
        )

    if not transcript.strip():
        warnings.append("No transcript was provided.")
    elif len(student_turns) == 0:
        warnings.append("No learner turns were detected in the transcript.")
    elif len(student_turns) < 2:
        warnings.append("Transcript has very few learner turns, so recommendations may be limited.")

    return TranscriptSignals(
        student_turn_count=len(student_turns),
        teacher_turn_count=len(teacher_turns),
        learner_examples=student_turns[:3],
        teacher_corrections=teacher_corrections[:3],
        possible_errors=possible_errors[:5],
        warnings=warnings,
    )


def _build_prompt(transcript: str, signals: TranscriptSignals) -> str:
    base_prompt = RECOMMENDATION_PROMPT_SPEC.content.replace(
        "{transcript}",
        transcript.strip() or "No transcript available.",
    )

    signal_context = {
        "student_turn_count": signals.student_turn_count,
        "teacher_turn_count": signals.teacher_turn_count,
        "learner_examples": signals.learner_examples,
        "teacher_corrections": signals.teacher_corrections,
        "possible_errors": signals.possible_errors,
        "warnings": signals.warnings,
    }

    return (
        f"{base_prompt}\n\n"
        "Additional transcript signals detected by the system:\n"
        f"{json.dumps(signal_context, ensure_ascii=False, indent=2)}\n\n"
        "Use these signals as evidence, but do not invent information that is not supported "
        "by the transcript."
    )


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


def _extract_json_object(raw: str) -> str:
    """
    Handles model outputs like:

    Here is the JSON:
    { ... }
    """
    text = _strip_json_fences(raw)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return text

    return text[start : end + 1]


def _normalize_report_key(key: str) -> str:
    normalized = key.strip().lower().replace(" ", "_").replace("-", "_")

    aliases = {
        "error_summary": "error_summary",
        "errors": "error_summary",
        "mistakes": "error_summary",
        "mistake_summary": "error_summary",
        "summary_of_errors": "error_summary",
        "error_analysis": "error_summary",
        "strengths": "strengths",
        "positive_points": "strengths",
        "what_went_well": "strengths",
        "areas_to_improve": "areas_to_improve",
        "area_to_improve": "areas_to_improve",
        "improvements": "areas_to_improve",
        "weaknesses": "areas_to_improve",
        "needs_work": "areas_to_improve",
        "suggested_next_topic": "suggested_next_topic",
        "next_topic": "suggested_next_topic",
        "next_lesson": "suggested_next_topic",
        "recommendation": "suggested_next_topic",
        "recommended_next_topic": "suggested_next_topic",
    }

    return aliases.get(normalized, normalized)


def _parse_loose_report(raw: str) -> dict[str, Any]:
    """
    Handles weak/local models that return label-style text instead of JSON.

    Example:
      Error summary: ...
      Strengths: ...
      Areas to improve: ...
      Suggested next topic: ...
    """
    parsed: dict[str, str] = {}

    for line in raw.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        normalized_key = _normalize_report_key(key)

        if normalized_key not in REPORT_FIELDS:
            continue

        parsed[normalized_key] = value.strip().strip('"').strip("'")

    if not parsed:
        raise RuntimeError("Recommendation generation failed: invalid JSON.")

    return parsed


def _parse_json(raw: str) -> dict[str, Any]:
    text = _extract_json_object(raw)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Recommendation model returned non-JSON output; trying loose parser.")
        return _parse_loose_report(raw)

    if not isinstance(parsed, dict):
        raise RuntimeError("Recommendation generation failed: expected JSON object.")

    return parsed


def _as_report_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return " ".join(str(item).strip() for item in value if str(item).strip())

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value).strip()


def _normalize_report(parsed: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in parsed.items():
        normalized[_normalize_report_key(str(key))] = value

    return {
        "error_summary": _as_report_text(normalized.get("error_summary")),
        "strengths": _as_report_text(normalized.get("strengths")),
        "areas_to_improve": _as_report_text(normalized.get("areas_to_improve")),
        "suggested_next_topic": _as_report_text(normalized.get("suggested_next_topic")),
        "raw_model_output": parsed,
    }


def _missing_report_fields(report: dict[str, Any]) -> list[str]:
    missing: list[str] = []

    for field_name in REPORT_FIELDS:
        value = str(report.get(field_name, "")).strip()
        if not value:
            missing.append(field_name)

    return missing


def _as_warning_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    return [text] if text else []


def _complete_report_with_fallback(
    *,
    report: dict[str, Any],
    fallback: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    missing = _missing_report_fields(report)

    if not missing:
        return report

    completed = dict(report)

    for field_name in missing:
        completed[field_name] = fallback.get(field_name, "")

    completed["warnings"] = [
        *_as_warning_list(report.get("warnings")),
        *_as_warning_list(fallback.get("warnings")),
        f"Recommendation model output was incomplete. Filled missing fields: {', '.join(missing)}.",
    ]
    completed["fallback_reason"] = reason
    completed["fallback_used_for_fields"] = missing

    return completed


def _fallback_warning_for_reason(failure_reason: str) -> str:
    if failure_reason.startswith("model_call_failed"):
        return (
            "Recommendation model was unavailable, so AfterClass used transcript-based "
            "rule analysis to generate a conservative recommendation."
        )

    if failure_reason.startswith("parse_failed"):
        return (
            "Recommendation model output could not be parsed, so AfterClass used a "
            "transcript-aware fallback."
        )

    if failure_reason.startswith("incomplete_model_output"):
        return (
            "Recommendation model output was incomplete, so AfterClass filled missing "
            "sections using transcript-aware fallback logic."
        )

    return "AfterClass used transcript-aware fallback logic for this recommendation."


def _build_transcript_aware_fallback(
    *,
    transcript: str,
    signals: TranscriptSignals,
    failure_reason: str,
) -> dict[str, Any]:
    """
    Last-resort recommendation generation.

    This should be conservative, evidence-based, and honest. It should not claim
    emotional, medical, or biometric insight.
    """
    learner_examples = " ".join(signals.learner_examples) or "No learner examples were detected."

    if signals.possible_errors:
        error_summary = " ".join(signals.possible_errors)
        areas_to_improve = (
            "Review the target grammar pattern and ask the learner to repeat corrected "
            "sentences in full. The transcript suggests work on present continuous forms: "
            "subject + am/is/are + verb-ing."
        )
        suggested_next_topic = (
            "Present continuous practice using short speaking drills and correction of "
            "base-verb forms after am/is/are."
        )
    elif signals.student_turn_count == 0:
        error_summary = "No learner turns were detected, so language errors could not be analyzed."
        areas_to_improve = (
            "Collect a longer transcript with learner responses before making detailed "
            "language recommendations."
        )
        suggested_next_topic = "Run a short diagnostic speaking activity with 3 to 5 learner responses."
    else:
        error_summary = (
            "Based on the available transcript, no specific repeated error pattern was detected "
            "by the rule-based checks."
        )
        areas_to_improve = (
            "Review the learner's sentence formation and ask follow-up questions that require "
            "complete sentence answers."
        )
        suggested_next_topic = "Short follow-up speaking drill based on the same lesson target."

    return {
        "error_summary": error_summary,
        "strengths": (
            "The learner participated in the activity and gave responses connected to the tutor "
            f"prompts. Example learner language: {learner_examples}"
        ),
        "areas_to_improve": areas_to_improve,
        "suggested_next_topic": suggested_next_topic,
        "warnings": [
            *signals.warnings,
            _fallback_warning_for_reason(failure_reason),
        ],
        "fallback_reason": failure_reason,
    }


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

    signals = _extract_transcript_signals(transcript)
    prompt = _build_prompt(transcript, signals)

    try:
        raw = await asyncio.to_thread(
            generate_with_backend,
            prompt,
            task="report",
            system_prompt=(
                "You are an expert EFL/ESL language coach generating teacher recommendations. "
                "Return only valid JSON. Do not infer emotions, diagnoses, or biometric signals."
            ),
        )
    except Exception as exc:
        logger.warning(
            "Recommendation model call failed; using transcript-aware fallback: %s",
            exc,
        )
        parsed = _build_transcript_aware_fallback(
            transcript=transcript,
            signals=signals,
            failure_reason=f"model_call_failed: {exc}",
        )
    else:
        try:
            parsed = _normalize_report(_parse_json(raw))
            fallback = _build_transcript_aware_fallback(
                transcript=transcript,
                signals=signals,
                failure_reason="incomplete_model_output",
            )
            parsed = _complete_report_with_fallback(
                report=parsed,
                fallback=fallback,
                reason="incomplete_model_output",
            )
        except RuntimeError as exc:
            logger.warning(
                "Recommendation parsing failed; using transcript-aware fallback: %s",
                exc,
            )
            parsed = _build_transcript_aware_fallback(
                transcript=transcript,
                signals=signals,
                failure_reason=f"parse_failed: {exc}",
            )

    report = RecommendationReport(
        chat_id=chat_id,
        transcript=transcript,
        error_summary=str(parsed.get("error_summary", "")),
        strengths=str(parsed.get("strengths", "")),
        areas_to_improve=str(parsed.get("areas_to_improve", "")),
        suggested_next_topic=str(parsed.get("suggested_next_topic", "")),
        raw_recommendations={
            "type": "recommendation_report",
            **parsed,
            "transcript_signals": {
                "student_turn_count": signals.student_turn_count,
                "teacher_turn_count": signals.teacher_turn_count,
                "learner_examples": signals.learner_examples,
                "teacher_corrections": signals.teacher_corrections,
                "possible_errors": signals.possible_errors,
                "warnings": signals.warnings,
            },
        },
    )

    logger.info("Recommendation analysis complete for chat_id=%s", chat_id)
    return report
