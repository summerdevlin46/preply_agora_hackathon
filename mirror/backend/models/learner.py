"""
backend/models/learner.py
Per-learner state tracked by the RL engine across sessions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import math


@dataclass
class ItemState:
    """RL state for a single exercise item (vocab word, conjugation, etc.)"""
    item_id: str
    attempts: int = 0
    successes: int = 0
    consecutive_successes: int = 0
    avg_response_time_ratio: float = 1.0    # actual / limit (lower = better)
    last_seen: Optional[datetime] = None
    difficulty_level: int = 1               # 1–5
    time_limit_s: int = 8                   # updated by RL
    retired: bool = False                   # mastered — skip until next session

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts > 0 else 0.0

    def ucb1_score(self, total_attempts: int) -> float:
        """Upper Confidence Bound score for item selection."""
        if self.attempts == 0:
            return float("inf")             # always try unseen items first
        exploitation = self.success_rate
        exploration = math.sqrt(2 * math.log(max(total_attempts, 1)) / self.attempts)
        return exploitation + exploration


@dataclass
class FormatStats:
    """Thompson Sampling state per exercise format per learner."""
    format_name: str
    successes: int = 1      # Beta prior alpha (start at 1 to avoid zero)
    failures: int = 1       # Beta prior beta

    def sample(self) -> float:
        """Sample from Beta distribution — used for Thompson Sampling."""
        import numpy as np
        return float(np.random.beta(self.successes, self.failures))


@dataclass
class LearnerProfile:
    """
    Complete RL state for a learner. Persisted to DynamoDB (or in-memory
    dict for hackathon fallback).
    """
    learner_id: str
    learner_name: str = "Student"
    item_states: dict[str, ItemState] = field(default_factory=dict)
    format_stats: dict[str, FormatStats] = field(default_factory=dict)
    session_count: int = 0
    total_exercises_attempted: int = 0
    weak_topics: list[str] = field(default_factory=list)   # persistently flagged
    strong_topics: list[str] = field(default_factory=list)
    last_session_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_item_state(self, item_id: str, default_time_limit: int = 8) -> ItemState:
        if item_id not in self.item_states:
            self.item_states[item_id] = ItemState(
                item_id=item_id,
                time_limit_s=default_time_limit
            )
        return self.item_states[item_id]

    def get_format_stats(self, format_name: str) -> FormatStats:
        if format_name not in self.format_stats:
            self.format_stats[format_name] = FormatStats(format_name=format_name)
        return self.format_stats[format_name]
