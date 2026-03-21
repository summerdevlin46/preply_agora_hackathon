"""
mirror/generation/cleanup.py

Calls GPT-4o to generate four narrative avatar prompts in one shot —
one per exercise mode — based on teacher notes and OCR worksheet JSON.

Output keys match the frontend ASSIGNMENT_TYPES ids exactly:
  avatar_conversation, vocabulary_challenge, read_aloud_review, error_detective
"""
import json
import logging

from openai import OpenAI

from mirror.config import get_env

logger = logging.getLogger(__name__)

CLEANUP_MODEL = "gpt-4o"

MODES = ["avatar_conversation", "vocabulary_challenge", "read_aloud_review", "error_detective"]

CLEANUP_SYSTEM_PROMPT = """
You are an expert EFL/ESL instructional designer specialising in AI avatar sessions.

You will receive:
- Teacher notes describing the lesson context, student level, and focus areas
- A parsed worksheet JSON with topic, vocabulary, and exercise structure

Your job is to generate FOUR distinct avatar session prompts — one per exercise mode.
Each prompt is a complete, standalone director's script for an AI speaking avatar.

CRITICAL RULES:
- Each prompt must be a single flowing narrative — no section headers, no bullet-point lists, no markdown
- Write in second person addressing the avatar directly ("You are...", "Your goal is...")
- Include: avatar name and role, student level and context, exact step-by-step session structure, vocabulary to reinforce, how to handle errors, how to close the session
- The structure must be explicit — number the steps so the avatar knows exactly what to do when
- Keep it grounded in the worksheet content — use the actual vocabulary, topics, and exercise types from the JSON
- Tone must match the mode: conversational for speaking, precise for writing, energetic for vocab, sharp for grammar
- Each prompt should be 150-250 words

The four modes are:
1. avatar_conversation — fluency and turn-taking through open spoken dialogue
2. vocabulary_challenge — spoken word production, definitions, and usage in sentences
3. read_aloud_review — student reads their own writing aloud, avatar gives structured feedback per step
4. error_detective — avatar reads sentences with deliberate errors, student identifies and explains the rule

Return ONLY valid JSON with exactly these four keys:
{
  "avatar_conversation": "...",
  "vocabulary_challenge": "...",
  "read_aloud_review": "...",
  "error_detective": "..."
}

No preamble, no markdown fences, no explanation.
""".strip()


def build_cleanup_user_message(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
    mode: str | None = None,
) -> str:
    parts = []

    if feedback and mode:
        parts.append(
            f"TEACHER FEEDBACK ON PREVIOUS VERSION OF '{mode}':\n{feedback.strip()}\n"
            f"Please revise only the '{mode}' prompt based on this feedback. "
            f"Return all four prompts — keep the other three unchanged.\n"
        )

    parts.append(f"TEACHER NOTES:\n{teacher_notes.strip() or 'None provided.'}")
    parts.append(f"WORKSHEET JSON:\n{json.dumps(worksheet_json, indent=2)}")

    return "\n\n".join(parts)


def run_cleanup(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
    mode: str | None = None,
    existing_prompts: dict | None = None,
) -> dict[str, str]:
    """
    Returns a dict with keys: avatar_conversation, vocabulary_challenge,
    read_aloud_review, error_detective.

    Pass feedback + mode for single-mode regeneration.
    Pass existing_prompts so unchanged modes are preserved if the model
    only returns the revised one.
    """
    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))

    user_message = build_cleanup_user_message(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
        mode=mode,
    )

    logger.info(
        "Running cleanup model (model=%s, feedback=%s, mode=%s)",
        CLEANUP_MODEL, bool(feedback), mode,
    )

    response = client.chat.completions.create(
        model=CLEANUP_MODEL,
        messages=[
            {"role": "system", "content": CLEANUP_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=2000,
        temperature=0.4,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Cleanup model returned invalid JSON:\n%s", raw)
        raise RuntimeError("Cleanup model did not return valid JSON.") from exc

    missing = [m for m in MODES if m not in parsed]
    if missing:
        if existing_prompts:
            for key in missing:
                if key in existing_prompts:
                    parsed[key] = existing_prompts[key]
                    logger.info("Preserved existing prompt for mode: %s", key)
        else:
            raise RuntimeError(f"Cleanup model missing modes: {missing}")

    empty = [m for m in MODES if not parsed.get(m, "").strip()]
    if empty:
        raise RuntimeError(f"Cleanup model returned empty prompts for: {empty}")

    return {m: parsed[m].strip() for m in MODES}


def run_single_mode_regeneration(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str,
    existing_prompts: dict,
) -> dict[str, str]:
    """
    Regenerates a single mode and returns the full four-prompt dict.
    TODO: log (mode, feedback, retry_count) for RL reward signal.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}. Must be one of {MODES}")

    return run_cleanup(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
        mode=mode,
        existing_prompts=existing_prompts,
    )
