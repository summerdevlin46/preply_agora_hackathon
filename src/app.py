import gradio as gr
import typer

from mirror.ui.components import build_exercise_section, build_worksheet_section
from mirror.ocr import parse_worksheet
from mirror.agents import run_exercise_workflow

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = typer.Typer()


def parse_and_store_worksheet(file):
    parsed = parse_worksheet(file)
    return parsed, parsed


def build_ui() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## 🪞 Mirror — Post-Lesson Language Coach")

        worksheet_state = gr.State("")

        student_name, lesson_topic, submit_btn, output_box = build_exercise_section()
        worksheet_file, parsed_text = build_worksheet_section()

        worksheet_file.change(
            fn=parse_and_store_worksheet,
            inputs=worksheet_file,
            outputs=[parsed_text, worksheet_state],
        )

        submit_btn.click(
            fn=run_exercise_workflow,
            inputs=[student_name, lesson_topic, worksheet_state],
            outputs=output_box,
        )

    return demo


@app.callback(invoke_without_command=True)
def main(
    port: int = typer.Option(7860, help="Port to run Gradio on"),
    share: bool = typer.Option(False, help="Create a public Gradio share link"),
):
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, share=share)


if __name__ == "__main__":
    app()
