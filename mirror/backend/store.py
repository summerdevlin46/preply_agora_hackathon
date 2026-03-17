"""
backend/store.py
Simple in-memory store for learner profiles and active sessions.
Used during the hackathon instead of DynamoDB to avoid setup overhead.

To upgrade to DynamoDB post-hackathon, swap out the InMemoryStore
for a DynamoDBStore that implements the same interface.
"""

from __future__ import annotations
import logging
from typing import Optional

from backend.models.session import MirrorSession, TeacherIntentPackage
from backend.models.learner import LearnerProfile

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Thread-unsafe in-memory store — fine for single-process hackathon demo."""

    def __init__(self):
        self._profiles: dict[str, LearnerProfile] = {}
        self._sessions: dict[str, MirrorSession] = {}
        self._pending_intents: dict[str, TeacherIntentPackage] = {}

    # --- Learner profiles ---

    def get_profile(self, learner_id: str, learner_name: str = "Student") -> LearnerProfile:
        if learner_id not in self._profiles:
            self._profiles[learner_id] = LearnerProfile(
                learner_id=learner_id,
                learner_name=learner_name,
            )
            logger.info(f"Created new learner profile: {learner_id}")
        return self._profiles[learner_id]

    def save_profile(self, profile: LearnerProfile) -> None:
        self._profiles[profile.learner_id] = profile

    # --- Sessions ---

    def get_session(self, session_id: str) -> Optional[MirrorSession]:
        return self._sessions.get(session_id)

    def save_session(self, session: MirrorSession) -> None:
        self._sessions[session.session_id] = session

    # --- Pending teacher intents ---

    def set_intent(self, learner_id: str, intent: TeacherIntentPackage) -> None:
        """Store a teacher's intent package until the student starts their session."""
        self._pending_intents[learner_id] = intent
        logger.info(f"Intent stored for learner {learner_id}")

    def get_intent(self, learner_id: str) -> Optional[TeacherIntentPackage]:
        return self._pending_intents.get(learner_id)

    def clear_intent(self, learner_id: str) -> None:
        self._pending_intents.pop(learner_id, None)

    def list_learners(self) -> list[str]:
        return list(self._profiles.keys())


# Global singleton — imported by all modules
store = InMemoryStore()
