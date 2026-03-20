"""
backend/teacher/worksheet_parser.py
Parses uploaded worksheets (PDF, DOCX, image) into structured exercise items.
Uses GPT-4o for intelligent extraction — handles messy real-world worksheet formats.
"""

from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import Optional

from backend.models.session import ParsedWorksheet, VocabItem, ConjugationItem
from backend.integrations.openai_client import chat_json, MODEL_SMART

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a PDF file."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX file."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text_from_image(file_bytes: bytes) -> str:
    """OCR fallback for image-based worksheets."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to the correct extractor based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext in (".png", ".jpg", ".jpeg"):
        return extract_text_from_image(file_bytes)
    else:
        # Try to decode as plain text
        try:
            return file_bytes.decode("utf-8")
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# GPT-4o structured extraction
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM = """You are a language teaching assistant that extracts structured 
learning items from worksheets. You always return valid JSON and nothing else."""

EXTRACTION_PROMPT = """
Extract all learnable items from this worksheet text. Return ONLY valid JSON with 
this exact structure — no explanation, no markdown, just JSON:

{{
  "vocab_items": [
    {{"term": "word or phrase", "definition": "meaning in English", "example": "example sentence or empty string"}}
  ],
  "conjugation_items": [
    {{"verb": "infinitive", "tense": "tense name", "target_forms": ["form1", "form2"], "subject_pronouns": ["yo", "tú"]}}
  ],
  "free_prompts": [
    "Any open-ended writing or speaking prompts from the worksheet as plain strings"
  ]
}}

If a category has no items, return an empty list for that key.

Worksheet text:
---
{text}
---
"""


def parse_worksheet(file_bytes: bytes, filename: str) -> ParsedWorksheet:
    """
    Full pipeline: extract text → GPT-4o structured extraction → ParsedWorksheet.
    """
    raw_text = extract_text(file_bytes, filename)

    if not raw_text.strip():
        logger.warning(f"No text extracted from {filename}")
        return ParsedWorksheet(raw_text="")

    try:
        data = chat_json(
            prompt=EXTRACTION_PROMPT.format(text=raw_text[:4000]),  # token safety
            system=EXTRACTION_SYSTEM,
            model=MODEL_SMART,
        )
    except Exception as e:
        logger.error(f"GPT-4o extraction failed: {e}")
        return ParsedWorksheet(raw_text=raw_text)

    vocab_items = [
        VocabItem(
            term=item.get("term", ""),
            definition=item.get("definition", ""),
            example=item.get("example", ""),
        )
        for item in data.get("vocab_items", [])
        if item.get("term")
    ]

    conjugation_items = [
        ConjugationItem(
            verb=item.get("verb", ""),
            tense=item.get("tense", ""),
            target_forms=item.get("target_forms", []),
            subject_pronouns=item.get("subject_pronouns", []),
        )
        for item in data.get("conjugation_items", [])
        if item.get("verb")
    ]

    return ParsedWorksheet(
        vocab_items=vocab_items,
        conjugation_items=conjugation_items,
        free_prompts=data.get("free_prompts", []),
        raw_text=raw_text,
    )


def parse_worksheet_from_text(text: str) -> ParsedWorksheet:
    """
    Parse a worksheet from plain text input (e.g. teacher types items directly).
    Useful for demo / testing without file upload.
    """
    try:
        data = chat_json(
            prompt=EXTRACTION_PROMPT.format(text=text[:4000]),
            system=EXTRACTION_SYSTEM,
            model=MODEL_SMART,
        )
    except Exception as e:
        logger.error(f"GPT-4o extraction failed: {e}")
        return ParsedWorksheet(raw_text=text)

    vocab_items = [
        VocabItem(term=i.get("term",""), definition=i.get("definition",""), example=i.get("example",""))
        for i in data.get("vocab_items", []) if i.get("term")
    ]
    conjugation_items = [
        ConjugationItem(verb=i.get("verb",""), tense=i.get("tense",""), target_forms=i.get("target_forms",[]))
        for i in data.get("conjugation_items", []) if i.get("verb")
    ]

    return ParsedWorksheet(
        vocab_items=vocab_items,
        conjugation_items=conjugation_items,
        free_prompts=data.get("free_prompts", []),
        raw_text=text,
    )
