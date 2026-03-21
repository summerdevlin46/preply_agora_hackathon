"""
mirror/generation/cleanup.py

Calls GPT-4o-mini to turn raw teacher notes + OCR worksheet JSON
into clean GOAL and USEFUL CONTEXT blocks for the avatar system prompt.
"""
import json
import logging

from openai import OpenAI

from mirror.config import get_env

logger = logging.getLogger(__name__)

CLEANUP_MODEL = "gpt-4o-mini"

CLEANUP_SYSTEM_PROMPT = """
You are an expert EFL/ESL instructional designer.

Your job is to take a teacher's rough notes and a parsed worksheet and produce two clean, structured sections for an AI speaking coach prompt.

Rules:
- Be concise and specific
- Use plain text only — no markdown, no bullet symbols, no asterisks
- The GOAL must describe a clear drill structure with a specific number of items
- The USEFUL CONTEXT must describe the exact error types or language patterns to target
- Do not invent content not implied by the teacher notes or worksheet
- Return valid JSON only, no preamble, no markdown fences

Return exactly this schema:
{
  "goal": "string",
  "useful_context": "string"
}
""".strip()


def build_cleanup_user_message(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
) -> str:
    parts = []

    if feedback:
        parts.append(f"TEACHER FEEDBACK ON PREVIOUS VERSION:\n{feedback.strip()}\n")
        parts.append("Please revise based on this feedback.\n")

    parts.append(f"TEACHER NOTES:\n{teacher_notes.strip() or 'None provided.'}")
    parts.append(f"WORKSHEET JSON:\n{json.dumps(worksheet_json, indent=2)}")

    return "\n\n".join(parts)


def run_cleanup(
    teacher_notes: str,
    worksheet_json: dict,
    feedback: str | None = None,
) -> tuple[str, str]:
    """
    Returns (goal_block, context_block) as plain strings.
    Raises RuntimeError if the model returns invalid JSON.
    """
    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))

    user_message = build_cleanup_user_message(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
    )

    logger.info("Running cleanup model (feedback=%s)", bool(feedback))

    response = client.chat.completions.create(
        model=CLEANUP_MODEL,
        messages=[
            {"role": "system", "content": CLEANUP_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=600,
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Cleanup model returned invalid JSON:\n%s", raw)
        raise RuntimeError(
            "Cleanup model did not return valid JSON."
        ) from exc

    goal = parsed.get("goal", "").strip()
    context = parsed.get("useful_context", "").strip()

    if not goal or not context:
        raise RuntimeError(
            "Cleanup model returned empty goal or useful_context."
        )

    return goal, context
