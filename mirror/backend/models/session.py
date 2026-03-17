"""
backend/models/session.py
Core data models for Mirror sessions, exercises, and learner state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExerciseType(str, Enum):
    VOCAB_DRILL = "vocab_drill"
    CONJUGATION = "conjugation"
    SPEAKING = "speaking"
    WRITING = "writing"
    MULTIPLE_CHOICE = "multiple_choice"


class PressureProfile(str, Enum):
    RELAXED = "relaxed"      # +4s on all timers
    MEDIUM = "medium"        # default timers
    INTENSE = "intense"      # -2s on all timers


class ResponseOutcome(str, Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"
    TIMEOUT = "timeout"


# ---------------------------------------------------------------------------
# Worksheet / Teacher models
# ---------------------------------------------------------------------------

@dataclass
class VocabItem:
    term: str
    definition: str
    example: str = ""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class ConjugationItem:
    verb: str
    tense: str
    target_forms: list[str]
    subject_pronouns: list[str] = field(default_factory=list)
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class ParsedWorksheet:
    vocab_items: list[VocabItem] = field(default_factory=list)
    conjugation_items: list[ConjugationItem] = field(default_factory=list)
    free_prompts: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class TeacherIntentPackage:
    session_id: str
    learner_id: str
    topics_covered: list[str]
    exercise_types: list[ExerciseType]
    time_limit_per_exercise_s: int
    total_session_duration_s: int
    worksheet: ParsedWorksheet
    teacher_note: str = ""
    pressure_profile: PressureProfile = PressureProfile.MEDIUM
    created_at: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Exercise models
# ---------------------------------------------------------------------------

@dataclass
class Exercise:
    exercise_id: str
    item_id: str                    # links back to vocab/conjugation item
    exercise_type: ExerciseType
    prompt: str                     # what the avatar says / shows
    expected_answer: str            # used for scoring
    hint: str                       # revealed after timeout
    time_limit_s: int
    difficulty_level: int = 1       # 1–5, updated by RL engine
    format_label: str = ""          # human-readable format description


@dataclass
class ExerciseResponse:
    exercise_id: str
    transcript: str                 # what the student said/wrote
    response_time_s: float
    outcome: ResponseOutcome
    thymia_score: Optional[ThymiaScore] = None
    reward: float = 0.0             # computed after scoring
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThymiaScore:
    accuracy: float         # 0.0–1.0
    fluency_score: float    # 0.0–1.0 (words per min normalized)
    hesitation_count: int
    confidence: float       # 0.0–1.0
    wpm: float
    transcript: str = ""


# ---------------------------------------------------------------------------
# Session model
# ---------------------------------------------------------------------------

@dataclass
class MirrorSession:
    session_id: str
    learner_id: str
    intent: TeacherIntentPackage
    exercise_queue: list[Exercise] = field(default_factory=list)
    completed_responses: list[ExerciseResponse] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    avatar_greeting: str = ""

    @property
    def is_complete(self) -> bool:
        time_elapsed = (datetime.utcnow() - self.started_at).seconds if self.started_at else 0
        return (
            time_elapsed >= self.intent.total_session_duration_s
            or len(self.exercise_queue) == 0
        )

    @property
    def current_exercise(self) -> Optional[Exercise]:
        return self.exercise_queue[0] if self.exercise_queue else None

    def pop_exercise(self) -> Optional[Exercise]:
        return self.exercise_queue.pop(0) if self.exercise_queue else None
