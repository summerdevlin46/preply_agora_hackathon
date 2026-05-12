import os
from collections.abc import Iterable

from mirror.models.model_config import (
    get_provider_config,
    get_provider_priority,
    get_provider_runtime_config,
    get_routing_provider,
)

VALID_PROVIDER_KINDS = {"bedrock", "openai_compatible", "mistral"}


def has_any_env(keys: Iterable[str]) -> bool:
    return any(bool(os.getenv(key)) for key in keys)


def is_real_secret(value: str | None) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()
    return normalized not in {"", "todo", "changeme", "none", "null", "placeholder"}


def is_provider_configured(provider_name: str) -> bool:
    provider = get_provider_runtime_config(provider_name)

    if not provider.enabled:
        return False

    if provider.kind == "openai_compatible":
        # Local OSS usually has a base URL and dummy API key.
        # Hosted OpenAI-compatible providers need a real API key.
        return bool(provider.base_url) or is_real_secret(provider.api_key)

    if provider.kind == "bedrock":
        config = get_provider_config(provider_name)
        if not bool(config.get("enabled", False)):
            return False

        return bool(
            os.getenv("AWS_PROFILE")
            or has_any_env(["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"])
        )

    if provider.kind == "mistral":
        return is_real_secret(provider.api_key) and bool(provider.model)

    return False


def select_provider() -> str:
    configured = get_routing_provider()

    if configured != "auto":
        provider = get_provider_runtime_config(configured)
        if provider.kind not in VALID_PROVIDER_KINDS:
            raise RuntimeError(
                f"Invalid provider kind for {configured!r}: {provider.kind!r}. "
                f"Use one of: {', '.join(sorted(VALID_PROVIDER_KINDS))}."
            )
        return configured

    for provider_name in get_provider_priority():
        if is_provider_configured(provider_name):
            return provider_name

    return "local_oss"
