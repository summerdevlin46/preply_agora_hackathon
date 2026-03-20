"""
backend/integrations/anam.py
Anam AI avatar integration.

Anam streams a photorealistic talking avatar that delivers exercises,
hints, and encouragement. For Option A (hackathon scope), we use Anam
in a request/response pattern: send text → get back an audio/video URL
or stream that Gradio plays.

NOTE: Update endpoint and auth pattern once Anam provides API docs
at the hackathon. Their SDK may differ from this REST pattern.
"""

from __future__ import annotations
import os
import logging
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ANAM_API_KEY = os.getenv("ANAM_API_KEY", "")
ANAM_PERSONA_ID = os.getenv("ANAM_PERSONA_ID", "")
ANAM_API_URL = "https://api.anam.ai/v1"


# Emotion → speaking style mapping
EMOTION_STYLES = {
    "encouraging": "Speak warmly and supportively, like a patient tutor.",
    "celebratory": "Speak with excitement and genuine praise.",
    "patient": "Speak slowly and gently, giving the learner time to think.",
    "neutral": "Speak clearly and calmly.",
}

# Pre-written fallback lines used when Anam is unavailable
FALLBACK_LINES = {
    "correct": [
        "Great job! That was exactly right.",
        "Perfect! Nice and fast too.",
        "Excellent work, keep it up!",
    ],
    "partial": [
        "Close! You've almost got it.",
        "Good try — let's look at that again.",
        "Nearly there, just a small adjustment needed.",
    ],
    "incorrect": [
        "Not quite — let's try again.",
        "That's okay, this one's tricky. Let me give you a hint.",
    ],
    "timeout": [
        "No worries — here's a hint to help you.",
        "Take your time. Think about...",
    ],
    "hint": [
        "Here's a clue:",
        "Think about it this way:",
    ],
}


class AnamClient:
    """
    Client for Anam avatar API.
    Falls back to text-only responses if ANAM_API_KEY is not set.
    """

    def __init__(self):
        self.api_key = ANAM_API_KEY
        self.persona_id = ANAM_PERSONA_ID
        self.available = bool(self.api_key and self.persona_id)
        if not self.available:
            logger.warning("ANAM credentials not set — avatar will be text-only fallback")

    def speak(
        self,
        text: str,
        emotion: str = "encouraging",
    ) -> dict:
        """
        Request the avatar to speak a line.

        Returns:
            dict with keys:
              - "video_url": URL to avatar video clip (if Anam available)
              - "audio_url": URL to audio-only clip (if Anam available)
              - "text": the script text (always present)
              - "available": bool — whether Anam was used or fallback
        """
        if self.available:
            try:
                return self._speak_with_anam(text, emotion)
            except Exception as e:
                logger.warning(f"Anam API failed ({e}), using text fallback")

        return {"text": text, "video_url": None, "audio_url": None, "available": False}

    def _speak_with_anam(self, text: str, emotion: str) -> dict:
        """
        Call Anam API to generate avatar speech.

        TODO: Update based on actual Anam SDK/API docs from hackathon.
        Their API may use a streaming approach or WebRTC — adjust accordingly.
        """
        style = EMOTION_STYLES.get(emotion, EMOTION_STYLES["neutral"])

        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{ANAM_API_URL}/personas/{self.persona_id}/speak",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "style_instruction": style,
                    "output_format": "mp4",
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "text": text,
            "video_url": data.get("video_url"),
            "audio_url": data.get("audio_url"),
            "available": True,
        }

    def build_greeting(
        self,
        learner_name: str,
        topics_covered: list[str],
        teacher_note: str,
        session_duration_min: int,
    ) -> str:
        """
        Build a personalised opening greeting script for the avatar.
        Uses GPT-4o so the greeting references the actual lesson content.
        """
        from backend.integrations.openai_client import chat, MODEL_FAST

        topics_str = ", ".join(topics_covered) if topics_covered else "today's lesson"
        note_str = f' Your teacher noted: "{teacher_note}"' if teacher_note else ""

        script = chat(
            prompt=(
                f"Write a warm, natural 2-sentence greeting from an AI language coach "
                f"named Mirror to a student named {learner_name}. "
                f"Reference that they just covered: {topics_str}.{note_str} "
                f"Tell them the session is {session_duration_min} minutes. "
                f"Sound like an encouraging tutor, not a robot. "
                f"Do NOT say 'certainly', 'absolutely', or 'of course'."
            ),
            system="You write natural, warm dialogue for an AI language tutor avatar.",
            model=MODEL_FAST,
        )
        return script.strip()

    def build_exercise_prompt(self, exercise_prompt: str, time_limit_s: int) -> str:
        """Wrap an exercise prompt with timing context for the avatar."""
        return f"{exercise_prompt} You have {time_limit_s} seconds."

    def build_hint(self, hint: str) -> str:
        """Wrap a hint for natural delivery."""
        return f"Here's a hint — {hint}"

    def build_feedback(self, outcome: str, reward: float) -> str:
        """Generate brief feedback line based on outcome."""
        import random
        lines = FALLBACK_LINES.get(outcome, FALLBACK_LINES["incorrect"])
        return random.choice(lines)


# Singleton
anam = AnamClient()
