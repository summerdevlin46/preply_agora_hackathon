from pathlib import Path


def ocr_image(path: Path) -> str:
    """
    OCR a single image file.
    TODO: implement with pytesseract or another backend.
    """
    raise NotImplementedError("Image OCR is not implemented yet.")


def ocr_pdf(path: Path) -> str:
    """
    OCR a scanned PDF by converting pages to images first.
    TODO: implement with pdf2image + pytesseract or another backend.
    """
    raise NotImplementedError("PDF OCR fallback is not implemented yet.")
