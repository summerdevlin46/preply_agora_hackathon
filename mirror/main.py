"""
main.py
Launch all three Mirror Gradio apps as tabs in a single interface.
Run with: python main.py

URLs:
  http://localhost:7860  — combined tabbed interface
  (or run each app individually on its own port)
"""

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from backend.teacher_app import build_teacher_app
from backend.student_app import build_student_app
from backend.dashboard_app import build_dashboard_app

teacher_app = build_teacher_app()
student_app = build_student_app()
dashboard_app = build_dashboard_app()

# Combine into a single tabbed interface
with gr.TabbedInterface(
    [teacher_app, student_app, dashboard_app],
    tab_names=["🧑‍🏫 Teacher Setup", "📚 Student Session", "📊 Dashboard"],
    title="🪞 Mirror — AI Language Coach",
) as demo:
    pass

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
