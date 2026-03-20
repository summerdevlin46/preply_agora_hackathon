import logging
from typing import Optional

from mirror.config import get_env
from mirror.models.huggingface_backend import generate_with_huggingface
from mirror.models.openai_backend import generate_with_openai

logger = logging.getLogger(__name__)


def generate_with_backend(prompt: str, model: Optional[str] = None) -> str:
    backend = get_env("MIRROR_MODEL_BACKEND", "openai").strip().lower()
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

        logger.error("Invalid model backend: %s", backend)
        return "Invalid model backend configuration. Use 'openai' or 'huggingface'."

    except Exception as exc:
        logger.exception("Model backend '%s' failed", backend)
        return (
            f"Model backend '{backend}' failed.\n"
            f"Error: {exc}\n\n"
            "Check API keys, model name, or backend configuration."
        )
