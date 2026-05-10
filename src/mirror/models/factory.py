import logging
from importlib import import_module
from typing import Optional

from mirror.config import get_env

logger = logging.getLogger(__name__)


def generate_with_openai(prompt: str, model: Optional[str] = None) -> str:
    backend = import_module("mirror.models.openai_backend")
    return backend.generate_with_openai(prompt=prompt, model=model)


def generate_with_huggingface(prompt: str, model: Optional[str] = None) -> str:
    backend = import_module("mirror.models.huggingface_backend")
    return backend.generate_with_huggingface(prompt=prompt, model=model)


def generate_with_local_oss(prompt: str, model: Optional[str] = None) -> str:
    backend = import_module("mirror.models.local_oss_backend")
    return backend.generate_with_local_oss(prompt=prompt, model=model)


def generate_with_bedrock(prompt: str, model: Optional[str] = None) -> str:
    backend = import_module("mirror.models.bedrock_backend")
    return backend.generate_with_bedrock(prompt=prompt, model=model)


def generate_with_backend(prompt: str, model: Optional[str] = None) -> str:
    backend = get_env("MIRROR_MODEL_BACKEND", "bedrock").strip().lower()
    logger.info("Using model backend: %s", backend)

    try:
        if backend == "openai":
            result = generate_with_openai(prompt=prompt, model=model)
            logger.info("OpenAI generation succeeded")
            return result

        if backend == "huggingface":
            result = generate_with_huggingface(prompt=prompt, model=model)
            logger.info("Hugging Face generation succeeded")
            return result

        if backend == "local_oss":
            result = generate_with_local_oss(prompt=prompt, model=model)
            logger.info("Local OSS generation succeeded")
            return result

        if backend == "bedrock":
            result = generate_with_bedrock(prompt=prompt, model=model)
            logger.info("Bedrock generation succeeded")
            return result

        logger.error("Invalid model backend: %s", backend)
        return "Invalid model backend configuration. Use 'bedrock', 'openai', 'huggingface', or 'local_oss'."

    except Exception as exc:
        logger.exception("Model backend '%s' failed", backend)
        return (
            f"Model backend '{backend}' failed.\n"
            f"Error: {exc}\n\n"
            "Check AWS credentials/region, model ID, or other backend configuration."
        )
