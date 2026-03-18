def parse_worksheet(file) -> str:
    """
    Accepts an uploaded file object from gr.File and returns extracted text.
    TODO: replace stub with real OCR (Tesseract, AWS Textract, etc.)

    Args:
        file: file path string passed by Gradio's gr.File component

    Returns:
        Extracted text as a plain string
    """
    # TODO: check file type (PDF vs image)
    # TODO: call OCR library
    # TODO: return cleaned text
    raise NotImplementedError


def clean_text(raw: str) -> str:
    """
    Post-process raw OCR output — strip noise, fix spacing.
    TODO: implement once real OCR is in place.
    """
    raise NotImplementedError
