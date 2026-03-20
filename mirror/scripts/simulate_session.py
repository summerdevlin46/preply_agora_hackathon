"""
scripts/simulate_session.py
Pre-populates the store with a realistic demo session so the dashboard
always has data to show, and the student app has a ready-to-go session.

Run before the demo: python scripts/simulate_session.py

This means the demo never depends on:
  - A live teacher filling in the form
  - A live API call completing successfully
  - The worksheet parser working perfectly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime

from backend.models.session import (
    ExerciseType,
    MirrorSession,
    ExerciseResponse,
    Exercise,
    ParsedWorksheet,
    PressureProfile,
    ResponseOutcome,
    TeacherIntentPackage,
    ThymiaScore,
    VocabItem,
    ConjugationItem,
)
from backend.models.learner import LearnerProfile
from backend.store import store


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_LEARNER_ID = "ana_garcia"
DEMO_LEARNER_NAME = "Ana García"
DEMO_SESSION_ID = "demo_001"

DEMO_VOCAB = [
    VocabItem("el camarero", "the waiter", "El camarero nos trajo la carta."),
    VocabItem("la carta", "the menu", "¿Me puede traer la carta, por favor?"),
    VocabItem("pedir", "to order", "Quiero pedir el menú del día."),
    VocabItem("la cuenta", "the bill", "¿Nos puede traer la cuenta?"),
    VocabItem("traer", "to bring", "¿Me puede traer un poco de agua?"),
]

DEMO_CONJUGATIONS = [
    ConjugationItem("querer", "subjunctive present", ["quiera", "quieras", "quiera", "queramos", "quieran"],
                    ["yo", "tú", "él/ella", "nosotros", "ellos"]),
    ConjugationItem("ser", "subjunctive present", ["sea", "seas", "sea", "seamos", "sean"],
                    ["yo", "tú", "él/ella", "nosotros", "ellos"]),
]

DEMO_WORKSHEET = ParsedWorksheet(
    vocab_items=DEMO_VOCAB,
    conjugation_items=DEMO_CONJUGATIONS,
    free_prompts=["Use subjunctive to express what you want at a restaurant."],
    raw_text="Demo worksheet: Restaurant vocabulary + subjunctive mood",
)

DEMO_INTENT = TeacherIntentPackage(
    session_id=DEMO_SESSION_ID,
    learner_id=DEMO_LEARNER_ID,
    topics_covered=["subjunctive mood", "restaurant vocabulary", "ser vs estar"],
    exercise_types=[ExerciseType.VOCAB_DRILL, ExerciseType.CONJUGATION, ExerciseType.SPEAKING],
    time_limit_per_exercise_s=8,
    total_session_duration_s=600,
    worksheet=DEMO_WORKSHEET,
    teacher_note="She kept confusing ser vs estar — focus conjugation there first.",
    pressure_profile=PressureProfile.MEDIUM,
)


# ---------------------------------------------------------------------------
# Simulate a completed session with realistic scores
# ---------------------------------------------------------------------------

SIMULATED_RESPONSES = [
    # (exercise_id, transcript, response_time, accuracy, fluency, hesitations, confidence, wpm)
    ("vocab_v1", "the waiter", 3.2, 1.0, 0.9, 0, 0.95, 120),
    ("vocab_v2", "the menu", 4.1, 1.0, 0.85, 1, 0.88, 110),
    ("conj_c1", "quiera", 6.8, 0.9, 0.7, 2, 0.72, 90),
    ("vocab_v3", "to order", 5.5, 1.0, 0.88, 0, 0.91, 115),
    ("conj_c2", "sea... hmm... sea", 7.9, 0.6, 0.55, 3, 0.58, 75),  # struggled
    ("speak_s1", "Quiero que el camarero quiera traernos la carta", 12.0, 0.8, 0.75, 2, 0.78, 95),
    ("vocab_v4", "the bill", 3.8, 1.0, 0.92, 0, 0.93, 122),
    ("conj_c2_retry", "sea", 4.2, 1.0, 0.82, 0, 0.85, 105),  # retry succeeded
]


def build_simulated_response(
    exercise_id: str,
    transcript: str,
    response_time: float,
    accuracy: float,
    fluency: float,
    hesitations: int,
    confidence: float,
    wpm: float,
) -> ExerciseResponse:
    thymia_score = ThymiaScore(
        accuracy=accuracy,
        fluency_score=fluency,
        hesitation_count=hesitations,
        confidence=confidence,
        wpm=wpm,
        transcript=transcript,
    )

    # Simple reward calculation
    correctness = 0.5 * accuracy
    time_limit = 8
    time_ratio = response_time / time_limit
    speed = 0.3 * max(0.0, 1.0 - time_ratio) if response_time <= time_limit else 0.0
    fluency_component = 0.2 * fluency
    reward = round(min(correctness + speed + fluency_component, 1.0), 4)

    if reward >= 0.7:
        outcome = ResponseOutcome.CORRECT
    elif reward >= 0.4:
        outcome = ResponseOutcome.PARTIAL
    else:
        outcome = ResponseOutcome.INCORRECT

    return ExerciseResponse(
        exercise_id=exercise_id,
        transcript=transcript,
        response_time_s=response_time,
        outcome=outcome,
        thymia_score=thymia_score,
        reward=reward,
    )


def run():
    print("🪞 Mirror — Seeding demo data...\n")

    # Create learner profile
    learner = LearnerProfile(
        learner_id=DEMO_LEARNER_ID,
        learner_name=DEMO_LEARNER_NAME,
        session_count=2,
        total_exercises_attempted=15,
    )
    store.save_profile(learner)
    print(f"✅ Learner profile created: {DEMO_LEARNER_ID}")

    # Store the pending intent (so teacher panel shows as "activated")
    store.set_intent(DEMO_LEARNER_ID, DEMO_INTENT)
    print(f"✅ Teacher intent stored for {DEMO_LEARNER_ID}")

    # Build a completed session for the dashboard
    responses = [build_simulated_response(*r) for r in SIMULATED_RESPONSES]

    session = MirrorSession(
        session_id=DEMO_SESSION_ID,
        learner_id=DEMO_LEARNER_ID,
        intent=DEMO_INTENT,
        exercise_queue=[],
        completed_responses=responses,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        avatar_greeting=(
            "Hi Ana! Great session today — you worked hard on subjunctive mood and "
            "restaurant vocabulary. Let's lock it in. We've got 10 minutes. Ready?"
        ),
    )
    store.save_session(session)
    print(f"✅ Demo session stored: {DEMO_SESSION_ID} ({len(responses)} responses)")

    correct = sum(1 for r in responses if r.reward >= 0.7)
    print(f"\n📊 Demo results: {correct}/{len(responses)} correct")
    print("   Items with low scores (will show in dashboard):")
    for r in responses:
        if r.reward < 0.6:
            print(f"   ⚠️  {r.exercise_id}: {r.reward:.0%} — '{r.transcript}'")

    print("\n✨ Done! Start the app: python main.py")
    print("   Then open http://localhost:7860")


if __name__ == "__main__":
    run()
