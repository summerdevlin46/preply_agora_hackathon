import shutil
from pathlib import Path


def _require_binary(binary_name: str, install_hint: str) -> None:
    if shutil.which(binary_name) is None:
        raise RuntimeError(
            f"Required system dependency '{binary_name}' is not installed. {install_hint}"
        )


def ocr_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Missing Python OCR dependencies. Install pytesseract and Pillow."
        ) from exc

    _require_binary(
        "tesseract",
        "Install Tesseract locally or use the project container.",
    )

    image = Image.open(path)
    return pytesseract.image_to_string(image)


def ocr_pdf(path: Path) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise RuntimeError(
            "Missing Python OCR dependencies. Install pdf2image and pytesseract."
        ) from exc

    _require_binary(
        "tesseract",
        "Install Tesseract locally or use the project container.",
    )
    _require_binary(
        "pdftoppm",
        "Install Poppler locally or use the project container.",
    )

    images = convert_from_path(str(path))
    parts: list[str] = []

    for i, image in enumerate(images, start=1):
        text = pytesseract.image_to_string(image)
        if text.strip():
            parts.append(f"[Page {i}]\n{text}")

    return "\n\n".join(parts)