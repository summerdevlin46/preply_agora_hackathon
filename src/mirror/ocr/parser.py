from mirror.ocr.file_types import validate_uploaded_file, is_pdf, is_supported_image
from mirror.ocr.pdf_text import extract_text_from_pdf
from mirror.ocr.image_ocr import ocr_image, ocr_pdf
from mirror.ocr.text_cleaning import clean_text


def parse_worksheet(file) -> str:
    path = validate_uploaded_file(file)

    if is_pdf(path):
        raw = extract_text_from_pdf(path)
        if not raw.strip():
            raw = ocr_pdf(path)
    elif is_supported_image(path):
        raw = ocr_image(path)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or image file.")

    cleaned = clean_text(raw)

    if not cleaned:
        return "No readable text could be extracted from the uploaded file."

    return cleaned
