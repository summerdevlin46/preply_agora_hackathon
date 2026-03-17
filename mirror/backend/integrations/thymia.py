"""
backend/integrations/thymia.py
Thymia API client for speech analysis and response scoring.
Falls back to Whisper + GPT-4o if THYMIA_API_KEY is not set or the
API call fails — so the rest of the system is never blocked.
"""

from __future__ import annotations
import os
import logging
from typing import Optional

import httpx
from dotenv import load_dotenv

from backend.models.session import ThymiaScore
from backend.integrations.openai_client import score_response_fallback

load_dotenv()
logger = logging.getLogger(__name__)

THYMIA_API_KEY = os.getenv("THYMIA_API_KEY", "")
THYMIA_API_URL = os.getenv("THYMIA_API_URL", "https://api.thymia.ai/v1")


class ThymiaClient:
    """
    Wrapper for Thymia's speech analysis API.

    NOTE FOR HACKATHON:
    We don't have the exact Thymia API spec yet — get it from their
    team at the event. The structure below follows their likely REST
    pattern. If the API differs, adjust _score_with_thymia() only;
    the rest of the codebase uses score_response() which handles fallback.
    """

    def __init__(self):
        self.api_key = THYMIA_API_KEY
        self.available = bool(self.api_key)
        if not self.available:
            logger.warning("THYMIA_API_KEY not set — using Whisper/GPT-4o fallback for scoring")

    def score_response(
        self,
        audio_bytes: bytes,
        expected_answer: str,
        exercise_prompt: str,
    ) -> ThymiaScore:
        """
        Score a student's spoken response.
        Tries Thymia first, falls back to Whisper + GPT-4o.
        """
        if self.available:
            try:
                return self._score_with_thymia(audio_bytes, expected_answer)
            except Exception as e:
                logger.warning(f"Thymia API failed ({e}), using fallback")

        return self._score_with_fallback(audio_bytes, expected_answer, exercise_prompt)

    def _score_with_thymia(
        self,
        audio_bytes: bytes,
        expected_answer: str,
    ) -> ThymiaScore:
        """
        Call Thymia API for speech scoring.

        TODO: Update endpoint / payload structure once Thymia team
        provides API docs at the hackathon.
        """
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{THYMIA_API_URL}/speech/score",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"audio": ("response.wav", audio_bytes, "audio/wav")},
                data={"expected_answer": expected_answer},
            )
            response.raise_for_status()
            data = response.json()

        # Map Thymia response fields to ThymiaScore
        # Adjust field names based on actual API response
        return ThymiaScore(
            accuracy=float(data.get("accuracy", 0.5)),
            fluency_score=float(data.get("fluency_score", 0.5)),
            hesitation_count=int(data.get("hesitation_count", 0)),
            confidence=float(data.get("confidence", 0.5)),
            wpm=float(data.get("wpm", 100)),
            transcript=data.get("transcript", ""),
        )

    def _score_with_fallback(
        self,
        audio_bytes: bytes,
        expected_answer: str,
        exercise_prompt: str,
    ) -> ThymiaScore:
        """Whisper transcription + GPT-4o-mini scoring."""
        data = score_response_fallback(audio_bytes, expected_answer, exercise_prompt)
        return ThymiaScore(
            accuracy=float(data.get("accuracy", 0.5)),
            fluency_score=float(data.get("fluency_score", 0.5)),
            hesitation_count=int(data.get("hesitation_count", 0)),
            confidence=float(data.get("confidence", 0.5)),
            wpm=float(data.get("wpm", 100)),
            transcript=data.get("transcript", ""),
        )

    def score_text_response(
        self,
        text: str,
        expected_answer: str,
        exercise_prompt: str,
    ) -> ThymiaScore:
        """
        Score a typed (writing exercise) response.
        No audio involved — goes straight to GPT-4o-mini.
        """
        from backend.integrations.openai_client import chat_json, MODEL_FAST

        data = chat_json(
            prompt=(
                f"Exercise: '{exercise_prompt}'\n"
                f"Expected: '{expected_answer}'\n"
                f"Student wrote: '{text}'\n\n"
                "Rate this written response. Return JSON:\n"
                "  accuracy (0.0-1.0)\n"
                "  fluency_score (0.0-1.0): clarity and naturalness of writing\n"
                "  hesitation_count (int): set to 0 for written responses\n"
                "  confidence (0.0-1.0): how confidently the answer was given\n"
                "  wpm (float): set to 0 for written responses\n"
                "Return ONLY valid JSON."
            ),
            system="You are a language learning assessment assistant.",
            model=MODEL_FAST,
        )
        data["transcript"] = text
        return ThymiaScore(**{k: data[k] for k in ThymiaScore.__dataclass_fields__})


# Singleton
thymia = ThymiaClient()
