import logging
from importlib import import_module
from typing import Optional

from mirror.models.model_config import get_provider_runtime_config
from mirror.models.provider_policy import select_provider

logger = logging.getLogger(__name__)


def generate_with_backend(
    prompt: str,
    model: Optional[str] = None,
    task: str = "default",
    system_prompt: str = "You are an expert language tutor.",
) -> str:
    provider_name = select_provider()
    provider = get_provider_runtime_config(provider_name, task=task)

    logger.info(
        "Using model provider: %s kind=%s task=%s",
        provider_name,
        provider.kind,
        task,
    )

    try:
        if provider.kind == "openai_compatible":
            backend = import_module("mirror.models.openai_compatible_backend")
            return backend.generate_with_openai_compatible(
                prompt=prompt,
                provider_name=provider_name,
                model=model,
                task=task,
                system_prompt=system_prompt,
            )

        if provider.kind == "bedrock":
            backend = import_module("mirror.models.bedrock_backend")
            return backend.generate_with_bedrock(
                prompt=prompt,
                model=model,
                task=task,
                system_prompt=system_prompt,
            )

        if provider.kind == "mistral":
            backend = import_module("mirror.models.mistral_backend")
            return backend.generate_with_mistral(
                prompt=prompt,
                provider_name=provider_name,
                model=model,
                task=task,
                system_prompt=system_prompt,
            )

        raise RuntimeError(
            f"Invalid provider kind {provider.kind!r} for provider {provider_name!r}."
        )

    except Exception as exc:
        logger.exception("Model provider '%s' failed", provider_name)
        return (
            f"Model provider '{provider_name}' failed.\n"
            f"Error: {exc}\n\n"
            "Check provider configuration, credentials, model ID, or local server status."
        )