"""
backend/teacher_app.py
Gradio interface for the teacher post-lesson setup.

The teacher:
  1. Uploads a worksheet (or pastes text)
  2. Tags topics covered + selects exercise types
  3. Sets time limits and session length
  4. Leaves a note (typed or voice)
  5. Hits "Activate Mirror" → intent package stored for the student
"""

from __future__ import annotations
import io
import logging
import uuid
from datetime import datetime

import gradio as gr
import numpy as np
import soundfile as sf

from backend.models.session import (
    ExerciseType,
    PressureProfile,
    TeacherIntentPackage,
)
from backend.teacher.worksheet_parser import parse_worksheet, parse_worksheet_from_text
from backend.integrations.openai_client import transcribe
from backend.store import store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Demo fixtures — pre-parsed for reliable hackathon demos
# ---------------------------------------------------------------------------

DEMO_WORKSHEET_TEXT = """
Vocabulary: el camarero (the waiter), la carta (the menu), querer (to want),
pedir (to order), traer (to bring), la cuenta (the bill)

Grammar: Subjunctive mood of querer
- yo quiera, tú quieras, él/ella quiera, nosotros queramos, ellos quieran

Exercises:
1. Write a sentence asking the waiter for the menu using subjunctive.
2. Use 'quiera' to express what you want for dinner.
"""

DEMO_LEARNERS = ["ana_garcia", "carlos_martinez", "demo_student"]


# ---------------------------------------------------------------------------
# Core function: build and store intent package
# ---------------------------------------------------------------------------

def activate_mirror(
    learner_id: str,
    worksheet_file,
    worksheet_text: str,
    topics: str,
    exercise_types: list[str],
    time_limit: int,
    session_length: int,
    teacher_note: str,
    voice_note,
    pressure: str,
) -> tuple[str, str]:
    """
    Parse worksheet, build TeacherIntentPackage, store it.
    Returns (status_message, parsed_items_preview).
    """
    if not learner_id:
        return "❌ Please select or enter a learner ID.", ""

    # --- Parse worksheet ---
    try:
        if worksheet_file is not None:
            with open(worksheet_file.name, "rb") as f:
                file_bytes = f.read()
            worksheet = parse_worksheet(file_bytes, worksheet_file.name)
        elif worksheet_text.strip():
            worksheet = parse_worksheet_from_text(worksheet_text)
        else:
            return "❌ Please upload a worksheet or paste worksheet text.", ""
    except Exception as e:
        logger.error(f"Worksheet parsing failed: {e}")
        return f"❌ Worksheet parsing failed: {str(e)}", ""

    # --- Transcribe voice note if provided ---
    if voice_note is not None and teacher_note.strip() == "":
        try:
            sample_rate, audio_array = voice_note
            buf = io.BytesIO()
            sf.write(buf, audio_array, sample_rate, format="WAV")
            teacher_note = transcribe(buf.getvalue(), "voice_note.wav")
            logger.info(f"Voice note transcribed: {teacher_note}")
        except Exception as e:
            logger.warning(f"Voice note transcription failed: {e}")

    # --- Map exercise type strings to enum ---
    type_map = {
        "Vocab drill": ExerciseType.VOCAB_DRILL,
        "Conjugation": ExerciseType.CONJUGATION,
        "Speaking": ExerciseType.SPEAKING,
        "Writing": ExerciseType.WRITING,
    }
    selected_types = [type_map[t] for t in exercise_types if t in type_map]
    if not selected_types:
        selected_types = [ExerciseType.VOCAB_DRILL, ExerciseType.SPEAKING]

    # --- Build intent package ---
    intent = TeacherIntentPackage(
        session_id=str(uuid.uuid4())[:8],
        learner_id=learner_id,
        topics_covered=[t.strip() for t in topics.split(",") if t.strip()],
        exercise_types=selected_types,
        time_limit_per_exercise_s=time_limit,
        total_session_duration_s=session_length * 60,
        worksheet=worksheet,
        teacher_note=teacher_note,
        pressure_profile=PressureProfile(pressure.lower()),
    )

    store.set_intent(learner_id, intent)

    # --- Build preview ---
    vocab_count = len(worksheet.vocab_items)
    conj_count = len(worksheet.conjugation_items)
    prompt_count = len(worksheet.free_prompts)

    vocab_preview = "\n".join(
        f"  • {v.term} → {v.definition}" for v in worksheet.vocab_items[:5]
    )
    conj_preview = "\n".join(
        f"  • {c.verb} ({c.tense}): {', '.join(c.target_forms[:3])}"
        for c in worksheet.conjugation_items[:3]
    )

    preview = (
        f"📋 Parsed worksheet:\n"
        f"  Vocab items: {vocab_count}\n"
        f"  Conjugation items: {conj_count}\n"
        f"  Open prompts: {prompt_count}\n\n"
    )
    if vocab_preview:
        preview += f"Vocabulary:\n{vocab_preview}\n\n"
    if conj_preview:
        preview += f"Conjugations:\n{conj_preview}"

    status = (
        f"✅ Mirror activated for {learner_id}!\n"
        f"Session ID: {intent.session_id}\n"
        f"Exercises: {', '.join(t.value for t in selected_types)}\n"
        f"Timer: {time_limit}s per exercise · {session_length} min total\n"
        f"Note: {teacher_note or '(none)'}"
    )

    return status, preview


def load_demo_worksheet() -> str:
    """Load the demo worksheet text into the text box."""
    return DEMO_WORKSHEET_TEXT


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def build_teacher_app() -> gr.Blocks:
    with gr.Blocks(title="Mirror — Teacher Setup", theme=gr.themes.Soft()) as app:

        gr.Markdown("""
        # 🪞 Mirror — Post-Lesson Setup
        *Activate a personalised exercise session for your student.*
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 👤 Student")
                learner_id = gr.Dropdown(
                    choices=DEMO_LEARNERS,
                    value="ana_garcia",
                    label="Select student",
                    allow_custom_value=True,
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📚 Topics & Exercises")
                topics = gr.Textbox(
                    label="Topics covered today",
                    placeholder="subjunctive mood, restaurant vocabulary, ser vs estar...",
                    value="subjunctive mood, restaurant vocabulary",
                )
                exercise_types = gr.CheckboxGroup(
                    choices=["Vocab drill", "Conjugation", "Speaking", "Writing"],
                    value=["Vocab drill", "Conjugation", "Speaking"],
                    label="Exercise types to include",
                )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⏱️ Timing")
                time_limit = gr.Slider(
                    minimum=3, maximum=60, value=8, step=1,
                    label="Seconds per exercise",
                )
                session_length = gr.Radio(
                    choices=[5, 10, 15, 20],
                    value=10,
                    label="Session length (minutes)",
                )
                pressure = gr.Radio(
                    choices=["Relaxed", "Medium", "Intense"],
                    value="Medium",
                    label="Pressure profile",
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📄 Worksheet")
                with gr.Tab("Upload file"):
                    worksheet_file = gr.File(
                        label="Upload worksheet (PDF, DOCX)",
                        file_types=[".pdf", ".docx", ".doc", ".txt"],
                    )
                with gr.Tab("Paste text"):
                    worksheet_text = gr.Textbox(
                        label="Paste worksheet content",
                        lines=6,
                        placeholder="Paste vocabulary lists, conjugation tables, or exercises...",
                    )
                    demo_btn = gr.Button("Load demo worksheet", size="sm", variant="secondary")
                    demo_btn.click(fn=load_demo_worksheet, outputs=worksheet_text)

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 💬 Note for Mirror")
                teacher_note = gr.Textbox(
                    label="Typed note",
                    placeholder="e.g. She kept mixing up ser vs estar — prioritise that...",
                    lines=2,
                )
                voice_note = gr.Audio(
                    sources=["microphone"],
                    label="Or record a voice note (optional)",
                    type="numpy",
                )

        activate_btn = gr.Button(
            "🚀 Activate Mirror for this student",
            variant="primary",
            size="lg",
        )

        with gr.Row():
            with gr.Column():
                status_out = gr.Textbox(label="Status", lines=6, interactive=False)
            with gr.Column():
                preview_out = gr.Textbox(label="Parsed worksheet preview", lines=8, interactive=False)

        activate_btn.click(
            fn=activate_mirror,
            inputs=[
                learner_id, worksheet_file, worksheet_text,
                topics, exercise_types, time_limit, session_length,
                teacher_note, voice_note, pressure,
            ],
            outputs=[status_out, preview_out],
        )

    return app


if __name__ == "__main__":
    app = build_teacher_app()
    app.launch(server_port=7860, share=False)
