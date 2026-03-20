from pathlib import Path


def extract_text_from_pdf(path: Path) -> str:
    """
    Extract embedded text from a PDF.
    Best for digital PDFs with selectable text.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for PDF text extraction. Install it with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    parts: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)

    return "\n\n".join(parts)
