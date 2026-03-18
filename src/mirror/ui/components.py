import gradio as gr


def build_exercise_section() -> tuple[gr.Textbox, gr.Textbox, gr.Button, gr.Textbox]:
    """
    Builds the learner exercise input/output section.
    Returns the components that app.py needs to wire up.
    """
    gr.Markdown("### Exercise Session")

    with gr.Row():
        # TODO: move student_name and lesson_topic textboxes here from app.py
        pass

    # TODO: move submit button here
    # TODO: move output_box here

    # TODO: return (student_name, lesson_topic, submit_btn, output_box)
    raise NotImplementedError


def build_worksheet_section() -> tuple[gr.File, gr.Textbox]:
    """
    Builds the teacher worksheet upload section.
    Returns the file input and parsed text output components.
    """
    gr.Markdown("### Teaching Materials")

    # TODO: add a gr.File component (accept PDFs and images)
    # TODO: add a gr.Textbox to show the parsed OCR text (read-only)

    # TODO: return (worksheet_file, parsed_text)
    raise NotImplementedError
