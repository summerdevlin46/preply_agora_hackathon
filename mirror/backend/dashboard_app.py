"""
backend/dashboard_app.py
Gradio dashboard showing session results.
Two views: student (how did I do?) and teacher (what needs work?).
"""

from __future__ import annotations
import logging

import gradio as gr

from backend.orchestrator.agent import generate_debrief
from backend.store import store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------

def load_student_dashboard(learner_id: str) -> tuple[str, str, str]:
    """
    Pull the most recent completed session for this learner.
    Returns (summary_text, exercise_table, recommendations).
    """
    if not learner_id:
        return "No learner selected.", "", ""

    # Find the most recent completed session for this learner
    session = None
    for sid, s in store._sessions.items():
        if s.learner_id == learner_id and s.completed_responses:
            session = s
            break

    if session is None:
        return f"No completed sessions found for {learner_id}.", "", ""

    learner = store.get_profile(learner_id)
    debrief = generate_debrief(session, learner)

    total = debrief["total_exercises"]
    correct = debrief["correct"]
    accuracy = debrief["accuracy_pct"]
    fluency = debrief["avg_fluency"]

    summary = (
        f"## Session Summary\n\n"
        f"**{correct} / {total}** exercises correct ({accuracy}%)\n\n"
        f"**Fluency score:** {fluency:.0%}\n\n"
        f"**Session ID:** {session.session_id}"
    )

    # Build exercise results table
    rows = []
    for r in session.completed_responses:
        outcome_emoji = {"correct": "✅", "partial": "🟡", "incorrect": "❌", "timeout": "⏰"}.get(
            r.outcome.value, "❓"
        )
        fluency_val = f"{r.thymia_score.fluency_score:.0%}" if r.thymia_score else "—"
        rows.append([
            r.exercise_id,
            outcome_emoji + " " + r.outcome.value.capitalize(),
            f"{r.response_time_s:.1f}s",
            fluency_val,
            f"{r.reward:.0%}",
        ])

    table = "| Exercise | Outcome | Time | Fluency | Score |\n"
    table += "|---|---|---|---|---|\n"
    for row in rows:
        table += "| " + " | ".join(row) + " |\n"

    # Items to review
    items_to_review = debrief.get("items_to_review", [])
    if items_to_review:
        recs = "**⚠️ Needs more practice:**\n" + "\n".join(f"- {i}" for i in items_to_review[:5])
    else:
        recs = "**🌟 Great work — no items flagged for review!**"

    return summary, table, recs


def load_teacher_dashboard(learner_id: str) -> tuple[str, str]:
    """
    Teacher view: debrief summary + what to focus on next lesson.
    """
    if not learner_id:
        return "No learner selected.", ""

    session = None
    for sid, s in store._sessions.items():
        if s.learner_id == learner_id and s.completed_responses:
            session = s
            break

    if session is None:
        return f"No completed session found for {learner_id}.", ""

    learner = store.get_profile(learner_id)
    debrief = generate_debrief(session, learner)

    summary = (
        f"**Student:** {learner.learner_name}\n\n"
        f"**Accuracy:** {debrief['correct']}/{debrief['total_exercises']} ({debrief['accuracy_pct']}%)\n\n"
        f"**Avg fluency:** {debrief['avg_fluency']:.0%}\n\n"
        f"---\n\n"
        f"{debrief['teacher_summary']}"
    )

    items = debrief.get("items_to_review", [])
    if items:
        focus = "**Suggested focus for next lesson:**\n" + "\n".join(f"- {i}" for i in items[:5])
    else:
        focus = "**All items showing good retention — consider introducing new material.**"

    return summary, focus


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

DEMO_LEARNERS = ["ana_garcia", "carlos_martinez", "demo_student"]


def build_dashboard_app() -> gr.Blocks:
    with gr.Blocks(title="Mirror — Dashboard", theme=gr.themes.Soft()) as app:

        gr.Markdown("# 🪞 Mirror — Progress Dashboard")

        with gr.Tab("Student View"):
            gr.Markdown("*See how your practice session went.*")
            with gr.Row():
                student_learner = gr.Dropdown(
                    choices=DEMO_LEARNERS,
                    value="ana_garcia",
                    label="Student ID",
                    allow_custom_value=True,
                    scale=2,
                )
                refresh_student = gr.Button("Load results", variant="primary", scale=1)

            student_summary = gr.Markdown("")
            student_table = gr.Markdown("")
            student_recs = gr.Markdown("")

            refresh_student.click(
                fn=load_student_dashboard,
                inputs=[student_learner],
                outputs=[student_summary, student_table, student_recs],
            )

        with gr.Tab("Teacher View"):
            gr.Markdown("*See what your student practised and what needs work.*")
            with gr.Row():
                teacher_learner = gr.Dropdown(
                    choices=DEMO_LEARNERS,
                    value="ana_garcia",
                    label="Student ID",
                    allow_custom_value=True,
                    scale=2,
                )
                refresh_teacher = gr.Button("Load debrief", variant="primary", scale=1)

            teacher_summary = gr.Markdown("")
            teacher_focus = gr.Markdown("")

            refresh_teacher.click(
                fn=load_teacher_dashboard,
                inputs=[teacher_learner],
                outputs=[teacher_summary, teacher_focus],
            )

    return app


if __name__ == "__main__":
    app = build_dashboard_app()
    app.launch(server_port=7862, share=False)
