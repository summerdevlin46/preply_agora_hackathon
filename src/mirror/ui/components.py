import gradio as gr


def build_exercise_section() -> tuple[gr.Textbox, gr.Textbox, gr.Button, gr.Textbox]:
    """
    Builds the learner exercise input/output section.
    Returns the components that app.py needs to wire up.
    """
    gr.Markdown("### Exercise Session")

    with gr.Row():
        student_name = gr.Textbox(label="Name")
        lesson_topic = gr.Textbox(label="Topic")

    submit_btn = gr.Button("Submit")
    output_box = gr.Textbox(label="Exercise")

    return student_name, lesson_topic, submit_btn, output_box


def build_worksheet_section() -> tuple[gr.File, gr.Textbox]:
    """
    Builds the teacher worksheet upload section.
    Returns the file input and parsed text output components.
    """
    gr.Markdown("### Teaching Materials")

    worksheet_file = gr.File(
        label="Upload worksheet",
        file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
    )

    parsed_text = gr.Textbox(
        label="Parsed OCR Text",
        interactive=False,
        lines=12,
    )

    return worksheet_file, parsed_text
