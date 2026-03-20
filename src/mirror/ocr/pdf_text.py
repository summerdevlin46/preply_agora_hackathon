from pathlib import Path
import re

def looks_like_useful_text(text: str, min_chars: int = 40) -> bool:
    """
    Heuristic: did PDF extraction actually work?

    We remove whitespace and check if there's enough signal.
    """
    if not text:
        return False

    visible = re.sub(r"\s+", "", text)
    return len(visible) >= min_chars

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
