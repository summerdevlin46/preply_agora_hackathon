from pathlib import Path

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def validate_uploaded_file(file) -> Path:
    if file is None:
        raise ValueError("No file was uploaded.")

    path = Path(file)

    if not path.exists():
        raise FileNotFoundError(f"Uploaded file not found: {path}")

    return path


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
