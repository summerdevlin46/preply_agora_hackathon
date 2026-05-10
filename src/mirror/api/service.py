import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from mirror.api.config_store import (
    get_chat_default_instructions,
    get_chat_instructions_by_id,
    get_chat_session_by_id,
    save_chat_instructions,
    save_homework_wrap,
)
from mirror.api.schemas import (
    ChatInstructionsResponse,
    ChatSessionResponse,
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    HomeworkCompletionRequest,
    HomeworkCompletionResponse,
    WorksheetParseResponse,
)
from mirror.generation.cleanup import MODES

_FALLBACK_PROMPTS = {
    "error_detective": (
        "You are Sofia, a sharp yet encouraging grammar coach for a B1 English student who has just worked through "
        "a worksheet on Cooking and the Present Continuous tense. "
        "You are in a focused one-on-one virtual language lab. Your tone is energetic, clear, and supportive. "
        "Use only plain text — no bolding, asterisks, or bullet points — because your responses go straight to speech. "
        "Use natural speech patterns like 'Okay...', 'Hmm, listen carefully...', or 'Good catch!' to feel authentic. "
        "Your goal is to drill the student on 8 sentences drawn from the worksheet's cooking context. "
        "All sentences contain deliberate present continuous errors using cooking vocabulary: "
        "fry, bake, boil, whisk, mix, pour, grill, chop, and the chocolate cake and cinnamon pancake recipes. "
        "Read these 8 sentences in order — each contains exactly one error: "
        "Sentence 1: I mixing the cake ingredients. "
        "Sentence 2: She is whisk all the ingredients together. "
        "Sentence 3: He pouring the batter into the cake tin. "
        "Sentence 4: I is bake the cake in the oven. "
        "Sentence 5: They are fry the onions in the pan. "
        "Sentence 6: We boils the pasta at the moment. "
        "Sentence 7: She is chop the vegetables right now. "
        "Sentence 8: I are eating the delicious chocolate cake. "
        "For each sentence follow a strict four-step loop: "
        "Step 1 — read the sentence aloud clearly without signalling that it contains an error. "
        "Step 2 — ask the student: does that sound right to you? "
        "Step 3 — wait for their correction. If they correct it, ask them to explain the grammar rule. "
        "Step 4 — confirm or clarify the rule, then say the corrected sentence before moving on. "
        "Never move to the next sentence without receiving and confirming a correction. "
        "Keep a running score. After all 8 sentences, give the final score and a brief summary of the rules "
        "the student struggled with — missing 'be' verb, wrong 'be' form, or missing -ing suffix. "
        "If asked anything outside the grammar drill, redirect warmly: "
        "'Let us stay focused on our cooking grammar drill for now — ready for the next sentence?'"
    ),
    "avatar_conversation": (
        "You are Leo, a warm and encouraging conversation coach working with a B1 English student who has just "
        "studied a Cooking and Present Continuous tense worksheet. "
        "You are running a relaxed one-on-one spoken conversation session. "
        "Use only plain text — no markdown, no bullet points — because your responses go directly to speech. "
        "Use natural fillers like 'Great!', 'Oh interesting!', or 'Tell me more...' to keep conversation flowing. "
        "Your goal is to guide the student through three conversational rounds using cooking as the context: "
        "Round 1 — ask what they are doing right now in the kitchen, or what they imagined cooking during the lesson. "
        "Encourage full present continuous sentences: I am mixing, she is baking, they are grilling. "
        "Round 2 — ask them to describe how to make a simple dish step by step, using present continuous throughout. "
        "Prompt with the worksheet's chocolate cake recipe if they are stuck: mix, whisk, pour, bake. "
        "Round 3 — ask a discussion question from the worksheet: Do you prefer cooking or baking? "
        "Do you ever watch cooking shows? What is your favourite dish to cook? "
        "Weave gentle error corrections into your replies by modelling the correct form naturally. "
        "Keep your turns short so the student does most of the talking. "
        "After Round 3, give one warm sentence of encouragement and name one thing they did especially well."
    ),
    "vocabulary_challenge": (
        "You are Max, an upbeat vocabulary coach working with a B1 English student on the Cooking worksheet. "
        "You are running a spoken word-production quiz. "
        "Use only plain text — no markdown — because your responses are converted to speech. "
        "Be enthusiastic: use phrases like 'Excellent!', 'You got it!', 'Close — try again!', or 'Nice work!' "
        "Your goal is to quiz the student on the cooking vocabulary from their worksheet in three phases. "
        "Phase 1 — Cooking verbs. Quiz these 8 verbs one at a time by describing the action without naming it: "
        "fry: you put food in hot oil in a pan; "
        "bake: you cook food in the oven, like a cake or bread; "
        "boil: you heat water or liquid until bubbles appear; "
        "whisk: you beat eggs or batter quickly with a tool to make it smooth; "
        "mix: you combine ingredients together by stirring; "
        "pour: you tip liquid from one container into another; "
        "grill: you cook food on a rack over direct heat; "
        "chop: you cut food into pieces with a knife. "
        "For each verb, wait for the student to name it, then ask them to use it in a present continuous sentence. "
        "Give up to two attempts before revealing the answer. "
        "Phase 2 — Food categories. Ask the student to name: starter, main course, dessert — using the worksheet's examples. "
        "Phase 3 — Revisit any words the student hesitated on and drill them once more. "
        "Keep a running tally throughout. Close with the score and one memory tip for the hardest words."
    ),
    "read_aloud_review": (
        "You are Priya, a calm and precise writing coach working with a B1 English student on the Cooking worksheet. "
        "You are running a spoken dictation drill using present continuous sentences from the worksheet. "
        "Use only plain text — no markdown — because your responses go directly to speech. "
        "Your tone is methodical and encouraging. "
        "Your goal is to dictate 6 sentences from the worksheet's cooking recipes and exercises, one at a time. "
        "Read these sentences in order: "
        "Sentence 1: She is mixing all the ingredients together. "
        "Sentence 2: He is whisking the batter until it is smooth with no bubbles. "
        "Sentence 3: I am pouring the batter into the cake tin. "
        "Sentence 4: She is baking the chocolate cake in the oven at 180 degrees. "
        "Sentence 5: They are frying the pancakes in a hot pan with sunflower oil. "
        "Sentence 6: We are grilling the vegetables on the barbecue at the moment. "
        "For each sentence: "
        "Step 1 — read the sentence clearly at natural speed. "
        "Step 2 — tell the student to type exactly what they heard into the chat. "
        "Step 3 — wait for their typed response, then give spoken feedback: confirm what was correct, "
        "name any spelling or grammar error specifically, and say the correct version. "
        "Step 4 — move to the next sentence only after giving feedback. "
        "After all 6 sentences, give a summary of error patterns — for example missing -ing, wrong spelling of "
        "whisking or pouring — and one focused spelling rule from the worksheet: "
        "words ending in -e drop the e before adding -ing, for example bake becomes baking. "
        "Close by telling the student their accuracy rate out of 6."
    ),
}

_FALLBACK_TASKS = {
    "error_detective": [
        {
            "title": "Spot the Mistake",
            "description": "Leo reads a cooking sentence with a present continuous error. Listen carefully — does it sound right? Say yes or give the corrected version.",
        },
        {
            "title": "Explain the Rule",
            "description": "When you find an error, Leo asks why it's wrong. Explain the grammar rule in your own words — for example: 'I needs am before mixing.'",
        },
        {
            "title": "Score & Summary",
            "description": "After all 8 sentences, Leo gives your score and reviews the rules you found tricky — missing 'be', wrong 'be' form, or missing -ing.",
        },
    ],
    "avatar_conversation": [
        {
            "title": "Kitchen Right Now",
            "description": "Sofia asks what you are doing in the kitchen right now. Answer using full present continuous sentences — I am mixing, she is baking, they are grilling.",
        },
        {
            "title": "Recipe Walk-Through",
            "description": "Sofia asks you to describe making a dish step by step. Use the chocolate cake recipe from your worksheet: mix, whisk, pour, bake.",
        },
        {
            "title": "Cooking Discussion",
            "description": "Sofia asks a question from the worksheet — do you prefer cooking or baking? Do you watch cooking shows? Answer naturally and listen for gentle corrections.",
        },
    ],
    "vocabulary_challenge": [
        {
            "title": "Cooking Verbs Quiz",
            "description": "Max describes each action without naming it. When you know the verb — fry, bake, boil, whisk, mix, pour, grill, or chop — say it aloud or type it.",
        },
        {
            "title": "Use It in a Sentence",
            "description": "After each correct answer, Max asks you to use the verb in a present continuous sentence about the worksheet recipes.",
        },
        {
            "title": "Missed Words Round",
            "description": "Max revisits any verbs you hesitated on. Listen to the description again and try once more before he reveals the answer.",
        },
    ],
    "read_aloud_review": [
        {
            "title": "Listen & Type",
            "description": "Priya reads a present continuous sentence from the cooking worksheet. Type exactly what you hear — she'll give feedback after each one.",
        },
        {
            "title": "Spoken Corrections",
            "description": "After each sentence, Priya tells you what was correct and names any spelling or grammar slip — then reads the correct version aloud.",
        },
        {
            "title": "Spelling Rule Recap",
            "description": "After 6 sentences, Priya summarises your error patterns and reviews the key spelling rule: words ending in -e drop the e before adding -ing — like bake → baking.",
        },
    ],
}

logger = logging.getLogger(__name__)

_PARSE_FAILURE_PREFIXES = (
    "Unsupported file type:",
    "No readable text could be extracted",
    "OCR error:",
)

_HOMEWORK_ANALYSIS_PROMPT = """You are writing a brief teacher-facing post-homework review.

Use the transcript below to identify concrete strengths and struggles.
Be specific and cite the transcript by line number when relevant.
If a student struggles with pronunciation or proper nouns, mention the exact line and quote the relevant excerpt.
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
    learner_turns = sum(
        1 for line in transcript_lines if ". USER:" in line
    )
    persona_turns = sum(
        1 for line in transcript_lines if ". PERSONA:" in line
    )

    return "\n".join(
        [
            (
                "Overall outcome: The session transcript was saved, but the "
                "automatic model-based analysis was unavailable."
            ),
            (
                "Strengths: Transcript captured "
                f"{message_count} turns ({learner_turns} learner, "
                f"{persona_turns} tutor)."
            ),
            (
                "- Struggles: Automatic analysis fallback was used because "
                f"{failure_reason}."
            ),
            (
                "- Struggles: Review the saved transcript manually for exact "
                "error patterns and correction quality."
            ),
            (
                "Recommended follow-up: Re-run homework analysis after "
                "restoring OpenAI access if you need a teacher-facing summary."
            ),
        ]
    )


def _generate_homework_analysis(transcript: str) -> str:
    from mirror.models.bedrock_backend import generate_text

    analysis = generate_text(
        system_prompt=(
            "You are writing a brief teacher-facing post-homework review. "
            "Be specific, cite the transcript by line number, and keep output concise."
        ),
        user_message=_HOMEWORK_ANALYSIS_PROMPT.format(transcript=transcript),
    ).strip()
    if not analysis:
        raise RuntimeError("empty response from model")

    return analysis

# Avatar config matching the frontend ASSIGNMENT_TYPES
_AVATAR_CONFIG = {
    "speaking": {"name": "Sofia", "emoji": "🧑‍🍳"},
    "vocab":    {"name": "Max",   "emoji": "🎤"},
    "writing":  {"name": "Priya", "emoji": "📋"},
    "grammar":  {"name": "Leo",   "emoji": "🕵️"},
}

_TASKS = {
    "speaking": [
        {"icon": "💬", "label": "Opening Question",  "content": "The avatar opens with a question about what you are doing right now. Answer in full present continuous sentences."},
        {"icon": "🗣️", "label": "Describe a Process", "content": "Walk through a process step by step using present continuous."},
        {"icon": "💡", "label": "Follow-Up",          "content": "The avatar asks a broader opinion question. Errors will be woven into corrections."},
    ],
    "vocab": [
        {"icon": "👂", "label": "Listen & Respond",   "content": "The avatar describes each word aloud. Say it when you know it, or type it in the chat."},
        {"icon": "🗣️", "label": "Use It in a Sentence", "content": "After each correct answer, use the word in a full sentence."},
        {"icon": "🔁", "label": "Missed Words Recap", "content": "The avatar revisits any words you hesitated on at the end."},
    ],
    "writing": [
        {"icon": "✏️", "label": "Type What You Hear",     "content": "The avatar reads a sentence aloud. Type exactly what you hear into the chat."},
        {"icon": "🔊", "label": "Listen for Corrections", "content": "The avatar gives spoken feedback after each sentence."},
        {"icon": "📊", "label": "Error Pattern Summary",  "content": "After all sentences, the avatar summarises patterns in your errors."},
    ],
    "grammar": [
        {"icon": "👂", "label": "Does That Sound Right?", "content": "The avatar reads a sentence and asks if it sounds correct. Say yes or give the correction."},
        {"icon": "📖", "label": "Explain the Rule",       "content": "When you spot an error, the avatar asks you to explain why it is wrong."},
        {"icon": "🏆", "label": "Score & Summary",        "content": "After all sentences, the avatar gives your score and reviews rules you found tricky."},
    ],
}

_TIPS = {
    "speaking": "The avatar waits for your complete answer before speaking. Take your time.",
    "vocab":    "All clues are spoken — you can type a word in chat if unsure how to pronounce it.",
    "writing":  "Type exactly what you hear — don't edit as you go. Corrections come after.",
    "grammar":  "Listen to the full sentence before deciding if it sounds right.",
}

_MODE_TIPS = {
    "avatar_conversation": _TIPS["speaking"],
    "vocabulary_challenge": _TIPS["vocab"],
    "read_aloud_review": _TIPS["writing"],
    "error_detective": _TIPS["grammar"],
}


async def parse_uploaded_worksheet(file: UploadFile) -> WorksheetParseResponse:
    from mirror.ocr.vision_parser import parse_worksheet_to_json

    suffix = Path(file.filename or "worksheet").suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        temp_path = Path(handle.name)
        content = await file.read()
        handle.write(content)

    try:
        worksheet_json = parse_worksheet_to_json(str(temp_path))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    finally:
        temp_path.unlink(missing_ok=True)

    return WorksheetParseResponse(
        filename=file.filename or temp_path.name,
        worksheet_json=worksheet_json,
        worksheet_text=worksheet_json.get("raw_text", ""),
    )


def generate_exercise(
    payload: ExerciseGenerationRequest,
) -> ExerciseGenerationResponse:
    from mirror.agents.exercise_workflow import run_prompt_workflow

    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Topic is required.",
        )

    # result is the full dict: {mode: prompt, ..., tasks: {mode: [...]}}
    using_fallback = False
    try:
        result, error = run_prompt_workflow(
            teacher_notes=payload.teacher_notes or topic,
            worksheet_json=payload.worksheet_json or {},
            feedback=payload.feedback or "",
            mode=payload.mode or "",
            existing_prompts=payload.existing_prompts or {},
            retry_count=payload.retry_count or 0,
        )
    except Exception as exc:
        logger.warning("Exercise generation failed, using demo fallback: %s", exc)
        result, error = {}, str(exc)

    if error:
        logger.warning("Workflow returned error, using demo fallback: %s", error)
        using_fallback = True
        result = {**_FALLBACK_PROMPTS, "tasks": _FALLBACK_TASKS}

    # Extract tasks before building avatar_prompts so they don't bleed in
    tasks = result.pop("tasks", {})
    avatar_prompts = {m: result[m] for m in MODES if m in result}
    if not avatar_prompts:
        using_fallback = True
        avatar_prompts = dict(_FALLBACK_PROMPTS)
        tasks = dict(_FALLBACK_TASKS)

    if using_fallback:
        logger.info("Serving demo fallback prompts for topic=%s", topic)

    # Save one chat_id per mode to SQLite
    # Frontend navigates to /chat/{chat_id} to launch Anam for that mode
    chat_ids = {}
    base_id = payload.chat_id or str(uuid.uuid4())
    for mode in MODES:
        prompt = avatar_prompts.get(mode, "")
        if not prompt:
            continue
        chat_id = f"{base_id}-{mode}"
        save_chat_instructions(
            chat_id=chat_id,
            anam_prompt=prompt,
            tasks=tasks.get(mode, []),
            tip=_MODE_TIPS.get(mode, ""),
        )
        chat_ids[mode] = chat_id

    return ExerciseGenerationResponse(
        chat_ids=chat_ids,
        learner_name=payload.learner_name,
        topic=topic,
        avatar_prompts=avatar_prompts,
        tasks=tasks,
    )


def get_default_chat_instructions() -> ChatInstructionsResponse:
    return ChatInstructionsResponse(instructions=get_chat_default_instructions())


def get_chat_instructions(chat_id: str) -> ChatInstructionsResponse:
    return ChatInstructionsResponse(
        instructions=get_chat_instructions_by_id(chat_id)
    )


def get_chat_session(chat_id: str) -> ChatSessionResponse:
    session = get_chat_session_by_id(chat_id)
    if session is None:
        return ChatSessionResponse(instructions=None)

    return ChatSessionResponse(**session)


def complete_homework(
    chat_id: str,
    payload: HomeworkCompletionRequest,
) -> HomeworkCompletionResponse:
    normalized_chat_id = chat_id.strip()
    total_messages = len(payload.messages)
    logger.info(
        "complete_homework started for chat_id=%s with %s incoming messages",
        normalized_chat_id or "<empty>",
        total_messages,
    )

    if not normalized_chat_id:
        logger.warning("complete_homework rejected request with empty chat_id")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chat id is required.",
        )

    transcript_lines: list[str] = []
    skipped_empty_messages = 0
    for index, message in enumerate(payload.messages, start=1):
        content = message.content.strip()
        if not content:
            skipped_empty_messages += 1
            continue

        interruption_suffix = " [interrupted]" if message.interrupted else ""
        transcript_lines.append(
            f"{index}. {message.role.upper()}: {content}{interruption_suffix}"
        )

    logger.info(
        (
            "complete_homework built transcript for chat_id=%s with %s lines "
            "(skipped_empty_messages=%s)"
        ),
        normalized_chat_id,
        len(transcript_lines),
        skipped_empty_messages,
    )

    if not transcript_lines:
        logger.warning(
            "complete_homework rejected chat_id=%s because transcript was empty after normalization",
            normalized_chat_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcript messages are required.",
        )

    transcript = "\n".join(transcript_lines)
    logger.info(
        "complete_homework requesting analysis for chat_id=%s (transcript_chars=%s)",
        normalized_chat_id,
        len(transcript),
    )

    try:
        analysis = _generate_homework_analysis(transcript)
        logger.info(
            "complete_homework generated analysis for chat_id=%s (analysis_chars=%s)",
            normalized_chat_id,
            len(analysis),
        )
    except Exception as exc:
        logger.exception(
            "complete_homework analysis generation failed for chat_id=%s; using fallback",
            normalized_chat_id,
        )
        analysis = _build_fallback_homework_analysis(
            transcript_lines=transcript_lines,
            failure_reason=str(exc),
        )
        logger.warning(
            "complete_homework fallback analysis created for chat_id=%s (analysis_chars=%s)",
            normalized_chat_id,
            len(analysis),
        )

    was_updated = save_homework_wrap(
        chat_id=normalized_chat_id,
        transcript=transcript,
        analysis=analysis,
    )
    if not was_updated:
        logger.error(
            "complete_homework could not persist results because chat config was missing for chat_id=%s",
            normalized_chat_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat config entry not found for id '{normalized_chat_id}'.",
        )

    logger.info(
        "complete_homework persisted transcript and analysis for chat_id=%s",
        normalized_chat_id,
    )
    return HomeworkCompletionResponse(analysis=analysis)
