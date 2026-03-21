"""
mirror/generation/cleanup.py

Calls GPT-4o to generate four narrative avatar prompts + 3 student tasks
per mode in one shot, based on teacher notes and OCR worksheet JSON.

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

Your job is to generate FOUR distinct avatar session prompts — one per exercise mode —
plus THREE student-facing tasks per mode.

PROMPT RULES:
- Each prompt must be a single flowing narrative — no section headers, no bullet points, no markdown
- Write in second person addressing the avatar directly ("You are...", "Your goal is...")
- Include: avatar name and role, student level and context, exact step-by-step session structure, vocabulary to reinforce, how to handle errors, how to close the session
- Number the steps explicitly so the avatar knows exactly what to do when
- Ground it in the worksheet content — use the actual vocabulary, topics, and exercise types
- Tone must match the mode: conversational for speaking, precise for writing, energetic for vocab, sharp for grammar
- Each prompt should be 150-250 words

TASK RULES:
- Each mode gets exactly 3 tasks
- Each task has a short "title" (2-4 words) and a "description" (1-2 sentences max, student-facing)
- Tasks describe what the STUDENT does, not what the avatar does
- Tasks follow the session arc: opening activity, main activity, closing/wrap-up

The four modes are:
1. avatar_conversation — fluency and turn-taking through open spoken dialogue
2. vocabulary_challenge — spoken word production, definitions, and usage in sentences
3. read_aloud_review — student reads their own writing aloud, avatar gives structured feedback per step
4. error_detective — THIS IS THE PRIMARY DEMO MODE. The avatar reads sentences with deliberate grammar errors drawn from the worksheet vocabulary. Use a strict four-step loop per sentence: read → ask student to find the mistake → wait for correction → confirm or clarify the rule. Use exactly 6 sentences with varied error types (missing 'be', wrong 'be' form, missing -ing, double subject). Keep a running score and close with a summary of rules the student struggled with. Never move to the next sentence without receiving and confirming a correction.

Return ONLY valid JSON with exactly this structure:
{
  "avatar_conversation": "full narrative prompt...",
  "vocabulary_challenge": "full narrative prompt...",
  "read_aloud_review": "full narrative prompt...",
  "error_detective": "full narrative prompt...",
  "tasks": {
    "avatar_conversation": [
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."}
    ],
    "vocabulary_challenge": [
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."}
    ],
    "read_aloud_review": [
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."}
    ],
    "error_detective": [
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."},
      {"title": "...", "description": "..."}
    ]
  }
}

No preamble, no markdown fences, no explanation outside the JSON.
""".strip()


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
            f"Please revise only the '{mode}' prompt and its tasks based on this feedback. "
            f"Return the full JSON — keep the other three modes unchanged.\n"
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
) -> dict:
    """
    Returns a dict with keys: avatar_conversation, vocabulary_challenge,
    read_aloud_review, error_detective, tasks.
    """
    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))

    user_message = build_cleanup_user_message(
        teacher_notes=teacher_notes,
        worksheet_json=worksheet_json,
        feedback=feedback,
        mode=mode,
    )

    full_input = f"{CLEANUP_SYSTEM_PROMPT}\n\n{user_message}"

    logger.info(
        "Running cleanup model (model=%s, feedback=%s, mode=%s)",
        CLEANUP_MODEL, bool(feedback), mode,
    )

    response = client.responses.create(
        model=CLEANUP_MODEL,
        input=full_input,
        max_output_tokens=2500,
    )

    raw = _extract_text(response).strip()

    # Strip markdown fences if model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Cleanup model returned invalid JSON:\n%s", raw)
        raise RuntimeError("Cleanup model did not return valid JSON.") from exc

    # Validate prompts
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

    # Validate tasks
    tasks = parsed.get("tasks", {})
    for m in MODES:
        mode_tasks = tasks.get(m, [])
        if len(mode_tasks) != 3:
            raise RuntimeError(
                f"Expected 3 tasks for mode '{m}', got {len(mode_tasks)}"
            )
        for task in mode_tasks:
            if "title" not in task or "description" not in task:
                raise RuntimeError(
                    f"Task in mode '{m}' missing title or description: {task}"
                )

    return {
        **{m: parsed[m].strip() for m in MODES},
        "tasks": tasks,
    }


def run_single_mode_regeneration(
    teacher_notes: str,
    worksheet_json: dict,
    mode: str,
    feedback: str,
    existing_prompts: dict,
) -> dict:
    """
    Regenerates a single mode and returns the full output dict.
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
