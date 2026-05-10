import json
import logging
import os
from pathlib import Path
from typing import Any

from mirror.models.bedrock_backend import generate_with_vision
from mirror.models.factory import generate_with_backend
from mirror.models.model_config import get_model_config, get_provider_runtime_config
from mirror.models.provider_policy import is_provider_configured
from mirror.ocr.cache import build_cache_key, load_cached_parse, save_cached_parse
from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file
from mirror.ocr.image_ocr import ocr_image, ocr_pdf
from mirror.ocr.pdf_text import extract_text_from_pdf, looks_like_useful_text
from mirror.ocr.pdf_utils import image_file_to_data_url, pdf_to_page_data_urls

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v3"

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


def _ocr_config() -> dict[str, Any]:
    config = get_model_config()
    value = config.get("ocr", {})
    return value if isinstance(value, dict) else {}


def _ocr_step_config(step_name: str) -> dict[str, Any]:
    value = _ocr_config().get(step_name, {})
    return value if isinstance(value, dict) else {}


def _ocr_priority() -> list[str]:
    configured = _ocr_config().get(
        "priority",
        ["pdf_text", "bedrock_vision", "mistral_ocr", "tesseract"],
    )
    return [str(item).strip() for item in configured if str(item).strip()]


def _is_step_enabled(step_name: str) -> bool:
    return bool(_ocr_step_config(step_name).get("enabled", True))


def _is_real_secret(value: str | None) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()
    return normalized not in {"", "todo", "changeme", "none", "null", "placeholder"}


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()

    if not text.startswith("```"):
        return text

    parts = text.split("```")
    if len(parts) < 2:
        return text

    fenced = parts[1].strip()
    if fenced.lower().startswith("json"):
        fenced = fenced[4:].strip()

    return fenced


def _parse_json_model_output(raw: str) -> dict[str, Any]:
    text = _strip_json_fences(raw)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Parser returned invalid JSON:\n%s", raw)
        raise RuntimeError("Worksheet parser did not return valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Worksheet parser returned JSON, but not a JSON object.")

    return parsed


def _structure_raw_text(raw_text: str) -> dict[str, Any]:
    prompt = f"{OCR_JSON_PROMPT}\n\nWorksheet text:\n{raw_text}"

    structured = generate_with_backend(
        prompt,
        task="ocr_structuring",
        system_prompt="You convert OCR text from educational worksheets into strict JSON.",
    )

    return _parse_json_model_output(structured)


def _parse_with_pdf_text(path: Path) -> dict[str, Any] | None:
    if not is_pdf(path):
        return None

    text = extract_text_from_pdf(path)
    if not looks_like_useful_text(text):
        logger.info("PDF text extraction did not produce enough useful text.")
        return None

    logger.info("Parsing worksheet using embedded PDF text.")
    return _structure_raw_text(text)


def _parse_with_tesseract(path: Path) -> dict[str, Any]:
    logger.info("Parsing worksheet using local Tesseract OCR.")

    if is_pdf(path):
        text = ocr_pdf(path)
    elif is_supported_image(path):
        text = ocr_image(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    if not looks_like_useful_text(text):
        raise RuntimeError("Tesseract OCR did not produce enough useful text.")

    return _structure_raw_text(text)


def _parse_with_bedrock_vision(path: Path) -> dict[str, Any]:
    step_config = _ocr_step_config("bedrock_vision")
    provider_name = str(step_config.get("provider", "bedrock"))

    if not is_provider_configured(provider_name):
        raise RuntimeError(f"Bedrock vision provider {provider_name!r} is not configured.")

    provider = get_provider_runtime_config(provider_name, task="ocr_structuring")

    if is_pdf(path):
        data_urls = pdf_to_page_data_urls(path)
    elif is_supported_image(path):
        data_urls = [image_file_to_data_url(path)]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    logger.info("Parsing worksheet using Bedrock vision provider=%s model=%s", provider_name, provider.model)

    text = generate_with_vision(
        prompt=OCR_JSON_PROMPT,
        data_urls=data_urls,
        model=provider.model,
        task="ocr_structuring",
    ).strip()

    return _parse_json_model_output(text)


def _parse_with_mistral_ocr(path: Path) -> dict[str, Any]:
    step_config = _ocr_step_config("mistral_ocr")

    api_key_env = str(step_config.get("api_key_env", "MISTRAL_API_KEY"))
    api_key = os.getenv(api_key_env)

    if not _is_real_secret(api_key):
        raise RuntimeError(f"{api_key_env} is not set.")

    try:
        from mistralai import Mistral
    except ImportError as exc:
        raise RuntimeError("mistralai is not installed.") from exc

    ocr_model = str(step_config.get("ocr_model", "mistral-ocr-latest"))
    chat_model = str(step_config.get("chat_model", "mistral-small-latest"))

    client = Mistral(api_key=api_key)

    logger.info("Uploading worksheet to Mistral OCR model=%s", ocr_model)

    with path.open("rb") as file:
        uploaded = client.files.upload(
            file={"file_name": path.name, "content": file},
            purpose="ocr",
        )

    try:
        signed = client.files.get_signed_url(file_id=uploaded.id)

        ocr_response = client.ocr.process(
            model=ocr_model,
            document={
                "type": "document_url",
                "document_url": signed.url,
            },
        )

        raw_text = "\n\n".join(page.markdown for page in ocr_response.pages)
    finally:
        client.files.delete(file_id=uploaded.id)

    if not looks_like_useful_text(raw_text):
        raise RuntimeError("Mistral OCR did not produce enough useful text.")

    logger.info("Structuring Mistral OCR output using chat model=%s", chat_model)

    chat_response = client.chat.complete(
        model=chat_model,
        messages=[
            {
                "role": "user",
                "content": f"{OCR_JSON_PROMPT}\n\nWorksheet text:\n{raw_text}",
            }
        ],
    )

    raw = chat_response.choices[0].message.content or ""
    return _parse_json_model_output(raw)


def _cache_model_fingerprint() -> str:
    parts: list[str] = []

    for step in _ocr_priority():
        if not _is_step_enabled(step):
            continue

        if step == "bedrock_vision":
            provider_name = str(_ocr_step_config(step).get("provider", "bedrock"))
            try:
                provider = get_provider_runtime_config(provider_name, task="ocr_structuring")
                parts.append(f"{step}:{provider.name}:{provider.model}")
            except Exception:
                parts.append(f"{step}:unconfigured")
            continue

        if step == "mistral_ocr":
            config = _ocr_step_config(step)
            parts.append(
                f"{step}:{config.get('ocr_model', 'mistral-ocr-latest')}:"
                f"{config.get('chat_model', 'mistral-small-latest')}"
            )
            continue

        if step == "pdf_text":
            parts.append("pdf_text")

        if step == "tesseract":
            parts.append("tesseract")

    return "+".join(parts) or "ocr"


def parse_worksheet_to_json(file) -> dict[str, Any]:
    path = validate_uploaded_file(file)

    cache_key = build_cache_key(
        path=path,
        model=_cache_model_fingerprint(),
        prompt_version=PROMPT_VERSION,
    )

    cached = load_cached_parse(cache_key)
    if cached is not None:
        logger.info("Using cached worksheet parse: %s", cache_key)
        return cached

    logger.info("Cache miss for worksheet parse: %s", cache_key)

    failures: list[str] = []

    for step in _ocr_priority():
        if not _is_step_enabled(step):
            logger.info("Skipping disabled OCR step: %s", step)
            continue

        try:
            if step == "pdf_text":
                parsed = _parse_with_pdf_text(path)
                if parsed is None:
                    continue

            elif step == "bedrock_vision":
                parsed = _parse_with_bedrock_vision(path)

            elif step == "mistral_ocr":
                parsed = _parse_with_mistral_ocr(path)

            elif step == "tesseract":
                parsed = _parse_with_tesseract(path)

            else:
                logger.warning("Unknown OCR step configured: %s", step)
                continue

            save_cached_parse(cache_key, parsed)
            logger.info("Saved worksheet parse to cache: %s", cache_key)
            return parsed

        except Exception as exc:
            logger.warning("OCR step %s failed: %s", step, exc)
            failures.append(f"{step}: {exc}")

    raise RuntimeError(
        "All worksheet parsing strategies failed.\n"
        + "\n".join(f"- {failure}" for failure in failures)
    )