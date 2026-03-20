from mirror.ocr.file_types import validate_uploaded_file, is_pdf, is_supported_image
from mirror.ocr.pdf_text import extract_text_from_pdf, looks_like_useful_text
from mirror.ocr.image_ocr import ocr_image, ocr_pdf
from mirror.ocr.text_cleaning import clean_text


def parse_worksheet(file) -> str:
    try:
        path = validate_uploaded_file(file)

        if is_pdf(path):
            raw = extract_text_from_pdf(path)
            if not looks_like_useful_text(raw):
                raw = ocr_pdf(path)

        elif is_supported_image(path):
            raw = ocr_image(path)

        else:
            return f"Unsupported file type: {path.suffix}"

        cleaned = clean_text(raw)

        return cleaned or "No readable text found."

    except RuntimeError as e:
        return str(e)