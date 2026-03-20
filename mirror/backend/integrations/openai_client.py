"""
backend/integrations/openai_client.py
Thin wrapper around the OpenAI API. Centralises model choices and
provides a clean interface for the rest of the codebase.
"""

from __future__ import annotations
import json
import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Model constants — easy to swap in one place
MODEL_SMART = "gpt-4o"          # orchestration, worksheet parsing, debrief
MODEL_FAST = "gpt-4o-mini"      # hint generation, quick scoring


def chat(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str = MODEL_SMART,
    json_mode: bool = False,
) -> str:
    """Single-turn chat completion. Returns the response text."""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1000,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def chat_json(prompt: str, system: str, model: str = MODEL_SMART) -> dict:
    """Chat completion that always returns parsed JSON."""
    raw = chat(prompt, system=system, model=model, json_mode=True)
    return json.loads(raw)


def transcribe(audio_bytes: bytes, filename: str = "response.wav") -> str:
    """
    Transcribe audio using Whisper. Used as a Thymia fallback and for
    teacher voice notes.
    """
    response = _client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes, "audio/wav"),
    )
    return response.text


def score_response_fallback(
    audio_bytes: bytes,
    expected_answer: str,
    exercise_prompt: str,
) -> dict:
    """
    Whisper + GPT-4o-mini fallback for when Thymia is unavailable.
    Returns a dict matching ThymiaScore structure.
    """
    transcript = transcribe(audio_bytes)

    result = chat_json(
        prompt=(
            f"Exercise: '{exercise_prompt}'\n"
            f"Expected answer: '{expected_answer}'\n"
            f"Student said: '{transcript}'\n\n"
            "Rate the student's response. Return JSON with keys:\n"
            "  accuracy (0.0-1.0): how correct the answer is\n"
            "  fluency_score (0.0-1.0): how fluent/confident the delivery was\n"
            "  hesitation_count (int): number of obvious hesitations\n"
            "  confidence (0.0-1.0): overall confidence impression\n"
            "  wpm (float): estimated words per minute\n"
            "Return ONLY valid JSON, no other text."
        ),
        system="You are a language learning assessment assistant. Be accurate and fair.",
        model=MODEL_FAST,
    )
    result["transcript"] = transcript
    return result
