import logging

from openai import APIConnectionError, OpenAI

from mirror.models.model_config import (
    get_generation_settings,
    get_provider_runtime_config,
)

logger = logging.getLogger(__name__)


def generate_with_openai_compatible(
    prompt: str,
    provider_name: str,
    model: str | None = None,
    task: str = "default",
    system_prompt: str = "You are an expert language tutor.",
) -> str:
    provider = get_provider_runtime_config(provider_name, task=task)
    generation = get_generation_settings(task=task)

    selected_model = model or provider.model

    if not selected_model:
        raise RuntimeError(f"No model configured for provider {provider_name!r}.")

    logger.info(
        "Using provider=%s kind=%s model=%s task=%s max_tokens=%s temperature=%s",
        provider.name,
        provider.kind,
        selected_model,
        task,
        generation.max_tokens,
        generation.temperature,
    )

    client = OpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key or "not-needed",
    )

    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=generation.max_tokens,
            temperature=generation.temperature,
        )
        return response.choices[0].message.content or ""

    except APIConnectionError as exc:
        raise RuntimeError(
            f"OpenAI-compatible provider {provider_name!r} is unreachable. "
            f"Base URL: {provider.base_url}"
        ) from exc