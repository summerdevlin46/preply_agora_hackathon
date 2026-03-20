import json
import logging
import os
from typing import Any

from openai import OpenAI

from mirror.config import get_env
from mirror.ocr.cache import build_cache_key, load_cached_parse, save_cached_parse
from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file
from mirror.ocr.pdf_utils import image_file_to_data_url, pdf_to_page_data_urls

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"

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


def _build_content(data_urls: list[str]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": OCR_JSON_PROMPT,
        }
    ]

    for url in data_urls:
        content.append(
            {
                "type": "input_image",
                "image_url": url,
            }
        )

    return content


def parse_worksheet_to_json(file) -> dict[str, Any]:
    """
    Parse a worksheet file (PDF or image) into structured JSON using OpenAI Vision.
    Uses a local file-based cache keyed by file contents + model + prompt version.
    """
    path = validate_uploaded_file(file)
    model = os.getenv("OPENAI_OCR_MODEL", "gpt-4o-mini")

    cache_key = build_cache_key(
        path=path,
        model=model,
        prompt_version=PROMPT_VERSION,
    )

    cached = load_cached_parse(cache_key)
    if cached is not None:
        logger.info("Using cached worksheet parse: %s", cache_key)
        return cached

    logger.info("Cache miss for worksheet parse: %s", cache_key)

    if is_pdf(path):
        data_urls = pdf_to_page_data_urls(path)
    elif is_supported_image(path):
        data_urls = [image_file_to_data_url(path)]
    else:
        raise ValueError(
            f"Unsupported file type: {path.suffix}. Please upload a PDF or image file."
        )

    client = OpenAI(api_key=get_env("OPENAI_API_KEY"))

    logger.info("Running vision parsing with model: %s", model)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": _build_content(data_urls),
            }
        ],
    )

    text = response.output_text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Vision parser returned invalid JSON:\n%s", text)
        raise RuntimeError(
            "Vision parser did not return valid JSON. "
            "Check the OCR prompt or the selected OCR model."
        ) from exc

    save_cached_parse(cache_key, parsed)
    logger.info("Saved worksheet parse to cache: %s", cache_key)

    return parsed
