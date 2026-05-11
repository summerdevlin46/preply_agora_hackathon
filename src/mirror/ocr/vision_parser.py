import json
import logging
import os
from pathlib import Path
from typing import Any

from mirror.generation.prompt_loader import load_prompt_spec
from mirror.models.factory import generate_with_backend
from mirror.models.model_config import get_model_config
from mirror.ocr.cache import build_cache_key, load_cached_parse, save_cached_parse
#TODO: what was is_supported_image? remove maybe
from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file
from mirror.ocr.pdf_text import extract_text_from_pdf, looks_like_useful_text

logger = logging.getLogger(__name__)


OCR_PROMPT_NAME = "ocr_structuring"
OCR_PROMPT_SPEC = load_prompt_spec(OCR_PROMPT_NAME)

OCR_JSON_PROMPT = OCR_PROMPT_SPEC.content
OCR_CACHE_PROMPT_VERSION = (
    f"{OCR_PROMPT_SPEC.name}:{OCR_PROMPT_SPEC.version}:{OCR_PROMPT_SPEC.sha256[:12]}"
)


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
        ["pdf_text", "mistral_ocr"],
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


        if step == "mistral_ocr":
            config = _ocr_step_config(step)
            parts.append(
                f"{step}:{config.get('ocr_model', 'mistral-ocr-latest')}:"
                f"{config.get('chat_model', 'mistral-small-latest')}"
            )
            continue

        if step == "pdf_text":
            parts.append("pdf_text")

    return "+".join(parts) or "ocr"


def parse_worksheet_to_json(file) -> dict[str, Any]:
    path = validate_uploaded_file(file)


    logger.info(
        "Using OCR prompt name=%s version=%s sha=%s",
        OCR_PROMPT_SPEC.name,
        OCR_PROMPT_SPEC.version,
        OCR_PROMPT_SPEC.sha256[:12],
    )

    cache_key = build_cache_key(
        path=path,
        model=_cache_model_fingerprint(),
        prompt_version=OCR_CACHE_PROMPT_VERSION,
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


            elif step == "mistral_ocr":
                parsed = _parse_with_mistral_ocr(path)


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
