import json
import logging
import os
from pathlib import Path
from typing import Any

from mirror.models.bedrock_backend import BEDROCK_MODEL, generate_with_vision
from mirror.ocr.cache import build_cache_key, load_cached_parse, save_cached_parse
from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file
from mirror.ocr.pdf_utils import image_file_to_data_url, pdf_to_page_data_urls

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"
MISTRAL_OCR_MODEL = "mistral-ocr-latest"
MISTRAL_CHAT_MODEL = "mistral-small-latest"

OCR_JSON_PROMPT = """
You are an expert educational document parser.

Extract this language-learning worksheet into structured JSON.

Rules:
- Return valid JSON only.
- Do not wrap the JSON in markdown.
- Do not summarize.
- Do not invent text.
- Preserve structure, numbering, and instructions.
- Clean obvious OCR noise but keep wording faithful.
- Preserve pedagogically meaningful sections.
- If answer keys or model answers are present, include them.
- If the level or topic is not explicit, infer only if it is obvious; otherwise use "unknown".

Return this schema:
{
  "title": string,
  "worksheet_type": string,
  "level": string,
  "topic": string,
  "instructions": [string],
  "sections": [
    {
      "heading": string,
      "task_type": string,
      "instructions": [string],
      "items": [string],
      "examples": [string]
    }
  ],
  "answer_key": [string],
  "notes": [string],
  "raw_text": string
}

Example:

Input worksheet snippet:
"Complete the sentences with the correct form of the verb.
1. She ____ to school every day.
2. They ____ football on Sundays."

Example JSON:
{
  "title": "Verb Practice",
  "worksheet_type": "Grammar Worksheet",
  "level": "unknown",
  "topic": "unknown",
  "instructions": ["Complete the sentences with the correct form of the verb."],
  "sections": [
    {
      "heading": "Main Exercise",
      "task_type": "Sentence Completion",
      "instructions": ["Complete the sentences with the correct form of the verb."],
      "items": [
        "She ____ to school every day.",
        "They ____ football on Sundays."
      ],
      "examples": []
    }
  ],
  "answer_key": [],
  "notes": [],
  "raw_text": "Complete the sentences with the correct form of the verb. 1. She ____ to school every day. 2. They ____ football on Sundays."
}
""".strip()


def _parse_with_bedrock(path: Path) -> dict[str, Any]:
    model = os.getenv("BEDROCK_MODEL", BEDROCK_MODEL)

    if is_pdf(path):
        data_urls = pdf_to_page_data_urls(path)
    elif is_supported_image(path):
        data_urls = [image_file_to_data_url(path)]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    logger.info("Running vision parsing via Bedrock (model=%s)", model)
    text = generate_with_vision(prompt=OCR_JSON_PROMPT, data_urls=data_urls, model=model).strip()
    return json.loads(text)


def _parse_with_mistral(path: Path) -> dict[str, Any]:
    from mistralai import Mistral

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    ocr_model = os.getenv("MISTRAL_OCR_MODEL", MISTRAL_OCR_MODEL)
    chat_model = os.getenv("MISTRAL_CHAT_MODEL", MISTRAL_CHAT_MODEL)

    logger.info("Uploading file to Mistral OCR (model=%s)", ocr_model)
    with open(path, "rb") as f:
        uploaded = client.files.upload(
            file={"file_name": path.name, "content": f},
            purpose="ocr",
        )

    try:
        signed = client.files.get_signed_url(file_id=uploaded.id)
        ocr_resp = client.ocr.process(
            model=ocr_model,
            document={"type": "document_url", "document_url": signed.url},
        )
        # Strip backslashes from OCR output — LaTeX notation (e.g. \circ, \mathrm)
        # produces invalid JSON escape sequences when the chat model echoes them back.
        raw_text = "\n\n".join(page.markdown for page in ocr_resp.pages).replace("\\", "")
    finally:
        client.files.delete(file_id=uploaded.id)

    logger.info("Structuring Mistral OCR output via chat (model=%s)", chat_model)
    chat_resp = client.chat.complete(
        model=chat_model,
        messages=[{"role": "user", "content": f"{OCR_JSON_PROMPT}\n\n{raw_text}"}],
    )
    raw = chat_resp.choices[0].message.content.strip()
    # strip markdown code fences if the model wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def parse_worksheet_to_json(file) -> dict[str, Any]:
    path = validate_uploaded_file(file)
    bedrock_model = os.getenv("BEDROCK_MODEL", BEDROCK_MODEL)
    mistral_model = os.getenv("MISTRAL_OCR_MODEL", MISTRAL_OCR_MODEL)

    cache_key = build_cache_key(
        path=path,
        model=f"{bedrock_model}+{mistral_model}",
        prompt_version=PROMPT_VERSION,
    )

    cached = load_cached_parse(cache_key)
    if cached is not None:
        logger.info("Using cached worksheet parse: %s", cache_key)
        return cached

    logger.info("Cache miss for worksheet parse: %s", cache_key)

    parsed: dict[str, Any] | None = None

    try:
        parsed = _parse_with_bedrock(path)
        logger.info("Bedrock parse succeeded")
    except Exception as exc:
        logger.warning("Bedrock parse failed (%s), trying Mistral fallback", exc)

    if parsed is None:
        if not os.getenv("MISTRAL_API_KEY"):
            raise RuntimeError(
                "Bedrock parse failed and MISTRAL_API_KEY is not set — no fallback available."
            )
        parsed = _parse_with_mistral(path)
        logger.info("Mistral fallback parse succeeded")

    save_cached_parse(cache_key, parsed)
    logger.info("Saved worksheet parse to cache: %s", cache_key)

    return parsed
