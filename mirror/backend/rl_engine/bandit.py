"""
backend/rl_engine/bandit.py
Multi-armed bandit RL engine for adaptive exercise selection.

Two bandits:
  1. Item selection  — UCB1 (Upper Confidence Bound)
  2. Format selection — Thompson Sampling (Beta distribution)

Plus spaced repetition: mastered items are retired from the current
session and flagged for re-introduction in a later session.
"""

from __future__ import annotations
import math
import logging
from datetime import datetime
from typing import Optional

import numpy as np

from backend.models.session import (
    Exercise,
    ExerciseResponse,
    ExerciseType,
    ResponseOutcome,
    TeacherIntentPackage,
    VocabItem,
    ConjugationItem,
)
from backend.models.learner import ItemState, LearnerProfile

logger = logging.getLogger(__name__)

# Mastery threshold — retire item after this many consecutive successes
MASTERY_THRESHOLD = 3
# Re-queue failed items after this many exercises
REQUEUE_AFTER = 3


# ---------------------------------------------------------------------------
# Reward computation
# ---------------------------------------------------------------------------

def compute_reward(response: ExerciseResponse, time_limit_s: int) -> float:
    """
    Compute RL reward in [0.0, 1.0] from a scored exercise response.

    Components:
      - Correctness  (0.0–0.5): primary signal
      - Speed        (0.0–0.3): faster relative to limit = better
      - Fluency      (0.0–0.2): Thymia/fallback fluency score
    """
    if response.thymia_score is None:
        # No score available — use outcome as proxy
        outcome_rewards = {
            ResponseOutcome.CORRECT: 0.8,
            ResponseOutcome.PARTIAL: 0.5,
            ResponseOutcome.INCORRECT: 0.1,
            ResponseOutcome.TIMEOUT: 0.0,
        }
        return outcome_rewards.get(response.outcome, 0.0)

    ts = response.thymia_score

    # Correctness
    correctness = 0.5 * ts.accuracy

    # Speed (only reward if answered within limit)
    if time_limit_s > 0 and response.response_time_s <= time_limit_s:
        time_ratio = response.response_time_s / time_limit_s
        speed = 0.3 * max(0.0, 1.0 - time_ratio)
    else:
        speed = 0.0

    # Fluency
    fluency = 0.2 * ts.fluency_score

    reward = correctness + speed + fluency
    return round(min(max(reward, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Item selection (UCB1)
# ---------------------------------------------------------------------------

def select_next_item(
    active_items: list[ItemState],
    learner: LearnerProfile,
) -> Optional[ItemState]:
    """
    Select the next exercise item using UCB1.
    Unseen items (attempts == 0) are always prioritised.
    Retired (mastered) items are skipped.
    """
    candidates = [i for i in active_items if not i.retired]
    if not candidates:
        return None

    total = learner.total_exercises_attempted or 1

    # Always try unseen items first
    unseen = [i for i in candidates if i.attempts == 0]
    if unseen:
        return unseen[0]

    # UCB1 scoring
    scored = [(item, item.ucb1_score(total)) for item in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


# ---------------------------------------------------------------------------
# Format selection (Thompson Sampling)
# ---------------------------------------------------------------------------

def select_format(
    learner: LearnerProfile,
    allowed_formats: list[ExerciseType],
) -> ExerciseType:
    """
    Select exercise format using Thompson Sampling.
    Learns which formats work best for this specific learner over time.
    """
    if len(allowed_formats) == 1:
        return allowed_formats[0]

    samples = []
    for fmt in allowed_formats:
        stats = learner.get_format_stats(fmt.value)
        sample = stats.sample()
        samples.append((fmt, sample))

    samples.sort(key=lambda x: x[1], reverse=True)
    return samples[0][0]


# ---------------------------------------------------------------------------
# Difficulty updates
# ---------------------------------------------------------------------------

def update_item_state(
    item_state: ItemState,
    reward: float,
    response_time_s: float,
) -> None:
    """Update item state after a response. Modifies in place."""
    item_state.attempts += 1
    item_state.last_seen = datetime.utcnow()

    if reward >= 0.7:
        item_state.successes += 1
        item_state.consecutive_successes += 1
    else:
        item_state.consecutive_successes = 0

    # Update avg response time ratio
    if item_state.time_limit_s > 0:
        ratio = response_time_s / item_state.time_limit_s
        item_state.avg_response_time_ratio = (
            0.7 * item_state.avg_response_time_ratio + 0.3 * ratio
        )

    # Retire if mastered
    if item_state.consecutive_successes >= MASTERY_THRESHOLD:
        item_state.retired = True
        logger.info(f"Item {item_state.item_id} retired (mastered)")

    # Difficulty escalation
    if reward > 0.85 and item_state.difficulty_level < 5:
        item_state.difficulty_level += 1
        item_state.time_limit_s = max(3, item_state.time_limit_s - 2)
    elif reward < 0.4 and item_state.difficulty_level > 1:
        item_state.difficulty_level -= 1
        item_state.time_limit_s = min(60, item_state.time_limit_s + 3)


def update_format_stats(
    learner: LearnerProfile,
    format_type: ExerciseType,
    reward: float,
) -> None:
    """Update Thompson Sampling Beta params for the used format."""
    stats = learner.get_format_stats(format_type.value)
    if reward >= 0.6:
        stats.successes += 1
    else:
        stats.failures += 1


# ---------------------------------------------------------------------------
# Exercise generation (from items)
# ---------------------------------------------------------------------------

def make_vocab_exercise(item: VocabItem, time_limit_s: int, difficulty: int) -> Exercise:
    """Generate a vocab drill exercise."""
    if difficulty <= 2:
        prompt = f"What does '{item.term}' mean?"
        expected = item.definition
        hint = f"It means: {item.definition[:20]}..."
    else:
        # Reverse direction at higher difficulty
        prompt = f"How do you say '{item.definition}' in Spanish?"
        expected = item.term
        hint = f"Starts with '{item.term[0]}'..."

    return Exercise(
        exercise_id=f"vocab_{item.item_id}",
        item_id=item.item_id,
        exercise_type=ExerciseType.VOCAB_DRILL,
        prompt=prompt,
        expected_answer=expected,
        hint=hint,
        time_limit_s=time_limit_s,
        difficulty_level=difficulty,
        format_label="Vocabulary",
    )


def make_conjugation_exercise(
    item: ConjugationItem,
    time_limit_s: int,
    difficulty: int,
) -> Exercise:
    """Generate a conjugation exercise."""
    # Pick a specific form to test based on difficulty
    if item.target_forms:
        idx = min(difficulty - 1, len(item.target_forms) - 1)
        target_form = item.target_forms[idx]
        pronoun = item.subject_pronouns[idx] if idx < len(item.subject_pronouns) else ""
        pronoun_str = f" for '{pronoun}'" if pronoun else ""
        prompt = f"Conjugate '{item.verb}' in the {item.tense}{pronoun_str}."
        expected = target_form
        hint = f"The ending should be '...{target_form[-2:]}'"
    else:
        prompt = f"Give the {item.tense} form of '{item.verb}'."
        expected = item.verb
        hint = f"Think about the {item.tense} pattern."

    return Exercise(
        exercise_id=f"conj_{item.item_id}",
        item_id=item.item_id,
        exercise_type=ExerciseType.CONJUGATION,
        prompt=prompt,
        expected_answer=expected,
        hint=hint,
        time_limit_s=time_limit_s,
        difficulty_level=difficulty,
        format_label="Conjugation",
    )


def make_speaking_exercise(
    item: VocabItem,
    time_limit_s: int,
    difficulty: int,
) -> Exercise:
    """Generate a speaking exercise using a vocab item."""
    prompt = f"Use '{item.term}' in a natural sentence."
    if difficulty >= 3 and item.example:
        prompt = f"Build on this example: '{item.example}'. Use '{item.term}' in your own sentence."

    return Exercise(
        exercise_id=f"speak_{item.item_id}",
        item_id=item.item_id,
        exercise_type=ExerciseType.SPEAKING,
        prompt=prompt,
        expected_answer=item.term,    # presence of term = success marker
        hint=f"Try: '{item.example}'" if item.example else f"Use '{item.term}' naturally.",
        time_limit_s=time_limit_s,
        difficulty_level=difficulty,
        format_label="Speaking",
    )
