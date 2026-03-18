import gradio as gr
import typer
from mirror.ui.components import build_exercise_section, build_worksheet_section
from mirror.utils.ocr import parse_worksheet

app = typer.Typer()


def generate_exercise(learner_name: str, topic: str) -> str:
    """
    Given a learner name and a topic, return a placeholder exercise string.
    TODO: replace with real orchestrator call later.
    """
    out = "Placeholder nothing burger exercise"
    print(out)
    #todo: need logger isntead
    return out
    ##raise NotImplementedError



def build_ui() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## 🪞 Mirror — Post-Lesson Language Coach")

        with gr.Row():
            student_name = gr.Textbox(label="Name")
            lesson_topic = gr.Textbox(label="Topic")

        # TODO: add a submit button
        submit_btn = gr.Button("Submit")
        #TODO, wiring requires this when clicking button instead
        ###generated_exercise = generate_exercise(learner_name="Summer", topic="present perfect idk")
        ###gr.Textbox(generated_exercise)

        # TODO: add a gr.Textbox for output (the generated exercise)
        output_box = gr.Textbox(label="Exercise")
        submit_btn.click(fn=generate_exercise, inputs=[student_name, lesson_topic], outputs=output_box)
    return demo

@app.command()
def serve(
    port: int = typer.Option(7860, help="Port to run Gradio on"),
    share: bool = typer.Option(False, help="Create a public Gradio share link"),
):
    """Launch the Mirror Gradio UI."""
    demo = build_ui()
    demo.launch(server_port=port, share=share)


if __name__ == "__main__":
    app()
