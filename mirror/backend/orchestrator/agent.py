"""
backend/orchestrator/agent.py
LangChain orchestrator agent. Merges teacher intent + learner history
to produce an ordered ExerciseQueue and personalised avatar greeting.
"""

from __future__ import annotations
import logging
import uuid
from datetime import datetime

from backend.models.session import (
    Exercise,
    ExerciseType,
    MirrorSession,
    TeacherIntentPackage,
)
from backend.models.learner import LearnerProfile
from backend.rl_engine.bandit import (
    make_vocab_exercise,
    make_conjugation_exercise,
    make_speaking_exercise,
    select_format,
)
from backend.integrations.anam import anam
from backend.integrations.openai_client import chat, MODEL_SMART

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exercise queue builder
# ---------------------------------------------------------------------------

def build_exercise_queue(
    intent: TeacherIntentPackage,
    learner: LearnerProfile,
) -> list[Exercise]:
    """
    Build the initial exercise queue from the teacher's intent package.
    Uses the learner profile to set initial difficulty and time limits.
    """
    exercises: list[Exercise] = []
    worksheet = intent.worksheet
    base_time = intent.time_limit_per_exercise_s

    allowed_types = set(intent.exercise_types)

    # --- Vocab items ---
    for vocab_item in worksheet.vocab_items:
        item_state = learner.get_item_state(vocab_item.item_id, base_time)
        if item_state.retired:
            continue

        # Choose format for this item using Thompson Sampling
        candidate_formats = [
            t for t in [ExerciseType.VOCAB_DRILL, ExerciseType.SPEAKING]
            if t in allowed_types
        ]
        if not candidate_formats:
            candidate_formats = [ExerciseType.VOCAB_DRILL]

        chosen_format = select_format(learner, candidate_formats)
        time_limit = item_state.time_limit_s
        difficulty = item_state.difficulty_level

        if chosen_format == ExerciseType.SPEAKING:
            exercises.append(make_speaking_exercise(vocab_item, time_limit, difficulty))
        else:
            exercises.append(make_vocab_exercise(vocab_item, time_limit, difficulty))

    # --- Conjugation items ---
    if ExerciseType.CONJUGATION in allowed_types:
        for conj_item in worksheet.conjugation_items:
            item_state = learner.get_item_state(conj_item.item_id, base_time)
            if item_state.retired:
                continue
            exercises.append(
                make_conjugation_exercise(
                    conj_item,
                    item_state.time_limit_s,
                    item_state.difficulty_level,
                )
            )

    # --- Free prompts as speaking exercises ---
    if ExerciseType.SPEAKING in allowed_types:
        for i, prompt_text in enumerate(worksheet.free_prompts[:3]):  # max 3 free prompts
            exercises.append(Exercise(
                exercise_id=f"free_{i}",
                item_id=f"free_{i}",
                exercise_type=ExerciseType.SPEAKING,
                prompt=prompt_text,
                expected_answer="",  # open-ended
                hint="Express yourself naturally — there's no single right answer.",
                time_limit_s=base_time * 2,  # more generous for open prompts
                format_label="Speaking",
            ))

    # Apply teacher note prioritisation
    if intent.teacher_note:
        exercises = _apply_teacher_note_ordering(exercises, intent.teacher_note)

    logger.info(f"Built exercise queue: {len(exercises)} items")
    return exercises


def _apply_teacher_note_ordering(
    exercises: list[Exercise],
    teacher_note: str,
) -> list[Exercise]:
    """
    Use GPT-4o to reorder exercises based on teacher note.
    Extracts keywords from the note and boosts matching items to the front.
    """
    if not exercises or not teacher_note:
        return exercises

    try:
        from backend.integrations.openai_client import chat_json, MODEL_FAST
        exercise_labels = [
            {"id": e.exercise_id, "prompt": e.prompt[:80]}
            for e in exercises
        ]
        result = chat_json(
            prompt=(
                f"Teacher note: '{teacher_note}'\n\n"
                f"Exercises: {exercise_labels}\n\n"
                "Return the exercise IDs reordered so the most relevant exercises "
                "to the teacher's note come first. Return JSON: {{\"ordered_ids\": [...]}}"
            ),
            system="You order language exercises by pedagogical priority.",
            model=MODEL_FAST,
        )
        ordered_ids = result.get("ordered_ids", [])
        id_to_exercise = {e.exercise_id: e for e in exercises}
        reordered = [id_to_exercise[eid] for eid in ordered_ids if eid in id_to_exercise]
        # Append any exercises not in the reordered list
        reordered_ids = set(ordered_ids)
        reordered += [e for e in exercises if e.exercise_id not in reordered_ids]
        return reordered
    except Exception as e:
        logger.warning(f"Teacher note ordering failed: {e} — using default order")
        return exercises


# ---------------------------------------------------------------------------
# Session builder
# ---------------------------------------------------------------------------

def build_session(
    intent: TeacherIntentPackage,
    learner: LearnerProfile,
) -> MirrorSession:
    """
    Full session setup: build exercise queue + generate avatar greeting.
    """
    exercise_queue = build_exercise_queue(intent, learner)

    greeting = anam.build_greeting(
        learner_name=learner.learner_name,
        topics_covered=intent.topics_covered,
        teacher_note=intent.teacher_note,
        session_duration_min=intent.total_session_duration_s // 60,
    )

    session = MirrorSession(
        session_id=intent.session_id,
        learner_id=intent.learner_id,
        intent=intent,
        exercise_queue=exercise_queue,
        avatar_greeting=greeting,
        started_at=datetime.utcnow(),
    )

    logger.info(
        f"Session {session.session_id} built: "
        f"{len(exercise_queue)} exercises, learner={learner.learner_id}"
    )
    return session


# ---------------------------------------------------------------------------
# Debrief generation
# ---------------------------------------------------------------------------

def generate_debrief(session: MirrorSession, learner: LearnerProfile) -> dict:
    """
    Generate a structured debrief after session completion.
    Returns data for both the student dashboard and teacher summary.
    """
    responses = session.completed_responses
    if not responses:
        return {"summary": "No exercises completed.", "teacher_note": "", "items_to_review": []}

    total = len(responses)
    correct = sum(1 for r in responses if r.reward >= 0.7)
    avg_fluency = (
        sum(r.thymia_score.fluency_score for r in responses if r.thymia_score)
        / max(1, sum(1 for r in responses if r.thymia_score))
    )

    # Items that still need work
    items_to_review = [
        r.exercise_id for r in responses
        if r.reward < 0.5
    ]

    # GPT-4o teacher summary
    response_summary = "\n".join(
        f"- {r.exercise_id}: reward={r.reward:.2f}, outcome={r.outcome}"
        for r in responses[:10]
    )

    teacher_summary = chat(
        prompt=(
            f"Student: {learner.learner_name}\n"
            f"Session results ({correct}/{total} correct):\n{response_summary}\n"
            f"Teacher note from before session: '{session.intent.teacher_note}'\n\n"
            "Write a 2-sentence teacher debrief: what went well, what to focus on next session. "
            "Be specific and actionable. No bullet points."
        ),
        system="You write concise, useful debrief notes for language tutors.",
        model=MODEL_SMART,
    )

    return {
        "total_exercises": total,
        "correct": correct,
        "accuracy_pct": round(100 * correct / total),
        "avg_fluency": round(avg_fluency, 2),
        "items_to_review": items_to_review,
        "teacher_summary": teacher_summary.strip(),
    }
