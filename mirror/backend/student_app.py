"""
backend/student_app.py
Gradio interface for the student exercise session (Option A).

Option A flow:
  1. Student selects their ID and clicks Start Session
  2. Avatar greeting is shown as text (+ video if Anam available)
  3. Exercise is displayed with its time limit
  4. Student records their answer (audio) or types it (writing exercises)
  5. Student clicks Submit Answer
  6. Thymia/fallback scores the response → feedback shown
  7. RL engine selects next exercise → repeat
  8. Session ends when queue is empty or time limit hit → redirect to dashboard
"""

from __future__ import annotations
import io
import logging
import time
from datetime import datetime
from typing import Optional

import gradio as gr
import numpy as np
import soundfile as sf

from backend.models.session import (
    Exercise,
    ExerciseResponse,
    ExerciseType,
    MirrorSession,
    ResponseOutcome,
)
from backend.models.learner import LearnerProfile
from backend.rl_engine.bandit import (
    compute_reward,
    select_next_item,
    update_item_state,
    update_format_stats,
    REQUEUE_AFTER,
)
from backend.orchestrator.agent import build_session, generate_debrief
from backend.integrations.thymia import thymia
from backend.integrations.anam import anam
from backend.store import store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_LEARNERS = ["ana_garcia", "carlos_martinez", "demo_student"]


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _audio_to_bytes(audio_numpy) -> Optional[bytes]:
    """Convert Gradio audio (sample_rate, np.array) to WAV bytes."""
    if audio_numpy is None:
        return None
    try:
        sample_rate, audio_array = audio_numpy
        buf = io.BytesIO()
        sf.write(buf, audio_array, sample_rate, format="WAV")
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        return None


def _outcome_from_reward(reward: float) -> ResponseOutcome:
    if reward >= 0.7:
        return ResponseOutcome.CORRECT
    elif reward >= 0.4:
        return ResponseOutcome.PARTIAL
    else:
        return ResponseOutcome.INCORRECT


def _format_exercise_display(exercise: Exercise) -> tuple[str, str, str]:
    """Returns (header, prompt_text, time_info) for display."""
    type_labels = {
        ExerciseType.VOCAB_DRILL: "📖 Vocabulary",
        ExerciseType.CONJUGATION: "✏️ Conjugation",
        ExerciseType.SPEAKING: "🎤 Speaking",
        ExerciseType.WRITING: "📝 Writing",
    }
    header = type_labels.get(exercise.exercise_type, "Exercise")
    time_info = f"⏱ {exercise.time_limit_s} seconds · Difficulty: {'⭐' * exercise.difficulty_level}"
    return header, exercise.prompt, time_info


# ---------------------------------------------------------------------------
# Core session functions
# ---------------------------------------------------------------------------

def start_session(learner_id: str) -> tuple:
    """
    Load the pending intent for this learner, build the session,
    and return the first exercise.
    Returns: (greeting, exercise_header, exercise_prompt, time_info,
               progress_text, session_id, exercise_id, start_time,
               is_writing, status_msg)
    """
    if not learner_id:
        empty = ("", "", "Please select a learner ID.", "", "", "", "", 0.0, False, "❌ No learner selected.")
        return empty

    intent = store.get_intent(learner_id)
    if intent is None:
        return ("", "", "No session prepared by your teacher yet. Ask your teacher to activate Mirror first.",
                "", "", "", "", 0.0, False, "❌ No pending session found.")

    learner = store.get_profile(learner_id)
    session = build_session(intent, learner)
    store.save_session(session.session_id)
    store.save_session(session)

    # Get avatar greeting
    greeting = session.avatar_greeting

    # Get first exercise
    exercise = session.current_exercise
    if exercise is None:
        return (greeting, "", "No exercises in queue.", "", session.session_id, "", "", 0.0, False,
                "⚠️ Session built but no exercises available.")

    header, prompt, time_info = _format_exercise_display(exercise)
    is_writing = exercise.exercise_type == ExerciseType.WRITING
    progress = f"Exercise 1 of {len(session.exercise_queue)} · Session: {session.session_id}"

    # Get avatar to speak the exercise (text only in Option A)
    avatar_script = anam.build_exercise_prompt(exercise.prompt, exercise.time_limit_s)
    anam.speak(avatar_script, emotion="encouraging")  # fires async, won't block

    return (
        greeting,
        header,
        prompt,
        time_info,
        progress,
        session.session_id,
        exercise.exercise_id,
        time.time(),          # exercise start time
        is_writing,
        f"✅ Session started! {len(session.exercise_queue)} exercises queued.",
    )


def submit_answer(
    session_id: str,
    exercise_id: str,
    start_time: float,
    audio_response,
    text_response: str,
) -> tuple:
    """
    Score the student's answer, update RL state, load next exercise.
    Returns: (feedback, next_header, next_prompt, next_time_info,
               progress, new_exercise_id, new_start_time, is_writing,
               hint_text, session_done)
    """
    session = store.get_session(session_id)
    if session is None:
        return ("Session not found.", "", "", "", "", "", 0.0, False, "", True)

    # Find current exercise
    current = session.current_exercise
    if current is None or current.exercise_id != exercise_id:
        # Exercise already advanced — edge case
        return ("", "", "", "", "", "", 0.0, False, "", session.is_complete)

    response_time = time.time() - start_time

    # --- Score the response ---
    is_writing = current.exercise_type == ExerciseType.WRITING

    if is_writing and text_response.strip():
        thymia_score = thymia.score_text_response(
            text_response.strip(),
            current.expected_answer,
            current.prompt,
        )
        transcript = text_response.strip()
    elif audio_response is not None:
        audio_bytes = _audio_to_bytes(audio_response)
        if audio_bytes:
            thymia_score = thymia.score_response(
                audio_bytes,
                current.expected_answer,
                current.prompt,
            )
            transcript = thymia_score.transcript
        else:
            thymia_score = None
            transcript = ""
    else:
        # No response — timeout
        thymia_score = None
        transcript = ""
        response_time = float(current.time_limit_s)

    # Determine outcome
    if not transcript and audio_response is None and not text_response:
        outcome = ResponseOutcome.TIMEOUT
        reward = 0.0
    else:
        reward = compute_reward(
            ExerciseResponse(
                exercise_id=exercise_id,
                transcript=transcript,
                response_time_s=response_time,
                outcome=ResponseOutcome.CORRECT,  # placeholder
                thymia_score=thymia_score,
                reward=0.0,
            ),
            current.time_limit_s,
        )
        outcome = _outcome_from_reward(reward)

    # Build response record
    response = ExerciseResponse(
        exercise_id=exercise_id,
        transcript=transcript,
        response_time_s=response_time,
        outcome=outcome,
        thymia_score=thymia_score,
        reward=reward,
    )
    session.completed_responses.append(response)

    # --- Update RL state ---
    learner = store.get_profile(session.learner_id)
    item_state = learner.get_item_state(current.item_id, current.time_limit_s)
    update_item_state(item_state, reward, response_time)
    update_format_stats(learner, current.exercise_type, reward)
    learner.total_exercises_attempted += 1
    store.save_profile(learner)

    # Re-queue failed items
    session.pop_exercise()
    if reward < 0.5 and outcome != ResponseOutcome.TIMEOUT:
        # Re-insert after REQUEUE_AFTER exercises in a different format
        session.exercise_queue.insert(
            min(REQUEUE_AFTER, len(session.exercise_queue)),
            current,
        )

    store.save_session(session)

    # --- Build feedback ---
    feedback_text = anam.build_feedback(outcome.value, reward)
    if thymia_score:
        feedback_text += f"\n\nFluency: {thymia_score.fluency_score:.0%} · Confidence: {thymia_score.confidence:.0%}"
        if thymia_score.transcript:
            feedback_text += f"\nYou said: \"{thymia_score.transcript}\""
    feedback_text += f"\n\nScore: {reward:.0%}"

    # --- Check session completion ---
    if session.is_complete:
        store.clear_intent(session.learner_id)
        debrief = generate_debrief(session, learner)
        store.save_session(session)
        return (
            feedback_text,
            "🏁 Session Complete",
            debrief.get("teacher_summary", "Session complete!"),
            f"Completed {len(session.completed_responses)} exercises",
            f"✅ {debrief['correct']}/{debrief['total_exercises']} correct · "
            f"Fluency: {debrief['avg_fluency']:.0%}",
            "", 0.0, False, "", True,
        )

    # --- Load next exercise ---
    next_exercise = session.current_exercise
    if next_exercise is None:
        return (feedback_text, "🏁 All done!", "", "", "", "", 0.0, False, "", True)

    next_header, next_prompt, next_time_info = _format_exercise_display(next_exercise)
    total = len(session.exercise_queue) + len(session.completed_responses)
    done = len(session.completed_responses)
    progress = f"Exercise {done + 1} of ~{total}"

    # Avatar speaks next exercise
    avatar_script = anam.build_exercise_prompt(next_exercise.prompt, next_exercise.time_limit_s)
    anam.speak(avatar_script, emotion="encouraging")

    return (
        feedback_text,
        next_header,
        next_prompt,
        next_time_info,
        progress,
        next_exercise.exercise_id,
        time.time(),
        next_exercise.exercise_type == ExerciseType.WRITING,
        "",       # hint cleared for new exercise
        False,    # session not done
    )


def reveal_hint(session_id: str, exercise_id: str) -> str:
    """Reveal the hint for the current exercise."""
    session = store.get_session(session_id)
    if session and session.current_exercise:
        hint = session.current_exercise.hint
        anam.speak(anam.build_hint(hint), emotion="patient")
        return f"💡 Hint: {hint}"
    return "No hint available."


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def build_student_app() -> gr.Blocks:
    with gr.Blocks(title="Mirror — Exercise Session", theme=gr.themes.Soft()) as app:

        gr.Markdown("# 🪞 Mirror — Your Practice Session")

        # Hidden state
        session_id_state = gr.State("")
        exercise_id_state = gr.State("")
        start_time_state = gr.State(0.0)
        session_done_state = gr.State(False)

        # --- Setup panel ---
        with gr.Group(visible=True) as setup_panel:
            gr.Markdown("### Select your student profile to begin")
            with gr.Row():
                learner_id = gr.Dropdown(
                    choices=DEMO_LEARNERS,
                    value="ana_garcia",
                    label="Your student ID",
                    allow_custom_value=True,
                    scale=2,
                )
                start_btn = gr.Button("▶ Start Session", variant="primary", scale=1)
            setup_status = gr.Textbox(label="Status", interactive=False, lines=2)

        # --- Session panel ---
        with gr.Group(visible=False) as session_panel:

            # Greeting
            greeting_box = gr.Textbox(
                label="🤖 Mirror says",
                interactive=False,
                lines=3,
            )

            gr.Markdown("---")

            # Exercise display
            exercise_header = gr.Markdown("**Exercise**")
            exercise_prompt = gr.Textbox(
                label="Your task",
                interactive=False,
                lines=2,
            )
            time_info = gr.Markdown("")
            progress_text = gr.Markdown("")

            # Hint
            hint_box = gr.Textbox(
                label="Hint",
                interactive=False,
                visible=False,
                lines=2,
            )
            hint_btn = gr.Button("💡 Show hint", size="sm", variant="secondary")

            gr.Markdown("---")

            # Response area — audio or text depending on exercise type
            with gr.Group() as audio_group:
                gr.Markdown("**🎤 Record your spoken answer, then click Submit**")
                audio_response = gr.Audio(
                    sources=["microphone"],
                    label="Your answer",
                    type="numpy",
                )

            with gr.Group(visible=False) as text_group:
                gr.Markdown("**📝 Type your answer below**")
                text_response = gr.Textbox(
                    label="Your written answer",
                    lines=3,
                    placeholder="Type your answer here...",
                )

            submit_btn = gr.Button("✅ Submit Answer", variant="primary", size="lg")

            # Feedback
            feedback_box = gr.Textbox(
                label="Feedback",
                interactive=False,
                lines=4,
            )

        # --- Completion panel ---
        with gr.Group(visible=False) as done_panel:
            gr.Markdown("## 🎉 Session Complete!")
            completion_summary = gr.Textbox(
                label="How you did",
                interactive=False,
                lines=4,
            )
            gr.Markdown("Your teacher will receive a debrief before your next lesson.")

        # ---------------------------------------------------------------------------
        # Event handlers
        # ---------------------------------------------------------------------------

        def on_start(learner_id_val):
            result = start_session(learner_id_val)
            (greeting, ex_header, ex_prompt, ex_time_info, progress,
             sid, eid, stime, is_writing, status) = result

            session_started = bool(sid)

            return (
                gr.update(visible=not session_started),  # setup_panel
                gr.update(visible=session_started),      # session_panel
                gr.update(visible=False),                # done_panel
                status,                                  # setup_status
                greeting,                                # greeting_box
                f"**{ex_header}**" if ex_header else "",  # exercise_header
                ex_prompt,                               # exercise_prompt
                ex_time_info,                            # time_info
                progress,                                # progress_text
                sid,                                     # session_id_state
                eid,                                     # exercise_id_state
                stime,                                   # start_time_state
                gr.update(visible=not is_writing),       # audio_group
                gr.update(visible=is_writing),           # text_group
                "",                                      # feedback_box
                gr.update(visible=False),                # hint_box
            )

        start_btn.click(
            fn=on_start,
            inputs=[learner_id],
            outputs=[
                setup_panel, session_panel, done_panel,
                setup_status, greeting_box,
                exercise_header, exercise_prompt, time_info, progress_text,
                session_id_state, exercise_id_state, start_time_state,
                audio_group, text_group,
                feedback_box, hint_box,
            ],
        )

        def on_submit(sid, eid, stime, audio, text):
            result = submit_answer(sid, eid, stime, audio, text)
            (feedback, next_header, next_prompt, next_time_info,
             progress, new_eid, new_stime, is_writing, hint, done) = result

            return (
                feedback,                                           # feedback_box
                f"**{next_header}**" if next_header else "",        # exercise_header
                next_prompt,                                        # exercise_prompt
                next_time_info,                                     # time_info
                progress,                                           # progress_text
                new_eid,                                            # exercise_id_state
                new_stime,                                          # start_time_state
                gr.update(visible=not is_writing),                  # audio_group
                gr.update(visible=is_writing),                      # text_group
                gr.update(value="", visible=False),                 # hint_box
                gr.update(visible=not done),                        # session_panel
                gr.update(visible=done),                            # done_panel
                next_prompt if done else "",                        # completion_summary
            )

        submit_btn.click(
            fn=on_submit,
            inputs=[session_id_state, exercise_id_state, start_time_state, audio_response, text_response],
            outputs=[
                feedback_box, exercise_header, exercise_prompt,
                time_info, progress_text,
                exercise_id_state, start_time_state,
                audio_group, text_group,
                hint_box,
                session_panel, done_panel, completion_summary,
            ],
        )

        def on_hint(sid, eid):
            hint_text = reveal_hint(sid, eid)
            return gr.update(value=hint_text, visible=True)

        hint_btn.click(
            fn=on_hint,
            inputs=[session_id_state, exercise_id_state],
            outputs=[hint_box],
        )

    return app


if __name__ == "__main__":
    app = build_student_app()
    app.launch(server_port=7861, share=False)
