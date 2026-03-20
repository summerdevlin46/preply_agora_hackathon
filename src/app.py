import gradio as gr
import typer

from mirror.ui.components import build_exercise_section, build_worksheet_section
from mirror.ocr import parse_worksheet

app = typer.Typer()


def generate_exercise(learner_name: str, topic: str) -> str:
    """
    Given a learner name and a topic, return a placeholder exercise string.
    TODO: replace with real orchestrator call later.
    """
    out = "Placeholder nothing burger exercise"
    print(out)  # TODO: replace with logger
    return out


def build_ui() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## 🪞 Mirror — Post-Lesson Language Coach")

        # Build reusable UI sections from components.py
        student_name, lesson_topic, submit_btn, output_box = build_exercise_section()
        worksheet_file, parsed_text = build_worksheet_section()

        # Wire app logic to the exercise section
        submit_btn.click(
            fn=generate_exercise,
            inputs=[student_name, lesson_topic],
            outputs=output_box,
        )

        # Wire OCR parsing to the worksheet section
        worksheet_file.change(
            fn=parse_worksheet,
            inputs=worksheet_file,
            outputs=parsed_text,
        )

    return demo

@app.callback(invoke_without_command=True)
def main(
    port: int = typer.Option(7860, help="Port to run Gradio on"),
    share: bool = typer.Option(False, help="Create a public Gradio share link"),
):
    """Launch the Mirror Gradio UI."""
    demo = build_ui()
    demo.launch(server_port=port, share=share)


if __name__ == "__main__":
    app()