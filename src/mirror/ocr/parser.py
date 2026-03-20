from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file
from mirror.ocr.image_ocr import ocr_image, ocr_pdf
from mirror.ocr.pdf_text import extract_text_from_pdf, looks_like_useful_text
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
            return f"Unsupported file type: {path.suffix}. Please upload a PDF or image file."

        cleaned = clean_text(raw)

        if not cleaned:
            return "No readable text could be extracted from the uploaded file."

        return cleaned

    except Exception as exc:
        return f"OCR error: {exc}"