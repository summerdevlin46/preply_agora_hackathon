from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/afterclass.toml")

@dataclass(frozen=True)
class LocalOssSettings:
    base_url: str
    api_key: str
    model: str

@dataclass(frozen=True)
class GenerationSettings:
    max_tokens: int
    temperature: float


@dataclass(frozen=True)
class ProviderSettings:
    model: str | None = None
    base_url: str | None = None
    region: str | None = None
    enabled: bool = False
    api_key: str | None = None


@dataclass(frozen=True)
class ProviderRuntimeConfig:
    name: str
    kind: str
    enabled: bool
    model: str
    base_url: str | None
    api_key: str | None
    region: str | None


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)

def _configured_value(
    provider: dict[str, Any],
    key: str,
    default: str | None = None,
) -> str | None:
    env_key = provider.get(f"{key}_env")
    if env_key:
        env_value = os.getenv(str(env_key))
        if env_value and env_value.strip():
            return env_value.strip()

    value = provider.get(key, default)
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _config_path() -> Path:
    configured = os.getenv("AFTERCLASS_CONFIG_PATH")
    path = Path(configured) if configured else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise RuntimeError(f"AfterClass config file not found: {path}")

    return path


@lru_cache(maxsize=1)
def get_model_config() -> dict[str, Any]:
    return _load_toml(_config_path())


def get_routing_provider() -> str:
    config = get_model_config()
    routing = config.get("model_routing", {})

    value = routing.get("provider", routing.get("backend", "auto"))
    return str(value).strip().lower()


def get_provider_priority() -> list[str]:
    config = get_model_config()
    priority = config.get("model_routing", {}).get(
        "priority",
        ["bedrock", "openai", "local_oss"],
    )
    return [str(item).strip().lower() for item in priority if str(item).strip()]



def get_generation_settings(task: str = "default") -> GenerationSettings:
    config = get_model_config()
    generation = config.get("generation", {})

    default_settings = generation.get("default", {})
    task_settings = generation.get(task, {})

    return GenerationSettings(
        max_tokens=int(
            task_settings.get(
                "max_tokens",
                default_settings.get("max_tokens", 1200),
            )
        ),
        temperature=float(
            task_settings.get(
                "temperature",
                default_settings.get("temperature", 0.2),
            )
        ),
    )


def get_provider_config(provider_name: str) -> dict[str, Any]:
    config = get_model_config()
    providers = config.get("providers", {})
    provider = providers.get(provider_name, {})

    if not isinstance(provider, dict):
        return {}

    return provider


def get_provider_api_key(provider_name: str) -> str | None:
    provider = get_provider_config(provider_name)

    api_key_env = provider.get("api_key_env")
    if api_key_env:
        value = os.getenv(str(api_key_env))
        if value:
            return value

    api_key_default = provider.get("api_key_default")
    if api_key_default:
        return str(api_key_default)

    return None

def get_local_oss_settings() -> LocalOssSettings:
    provider = get_provider_config("local_oss")

    base_url = _configured_value(
        provider,
        "base_url",
        "http://127.0.0.1:8081/v1",
    )
    model = _configured_value(
        provider,
        "model",
        "HuggingFaceTB/SmolLM2-360M-Instruct",
    )
    api_key = get_provider_api_key("local_oss") or "local-not-used"

    if not base_url or not model:
        raise RuntimeError("local_oss provider is missing base_url or model.")

    return LocalOssSettings(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )


def get_task_model(provider_name: str, task: str = "default") -> str | None:
    provider = get_provider_config(provider_name)

    task_models = provider.get("task_models", {})
    if isinstance(task_models, dict) and task in task_models:
        value = task_models[task]
        return str(value).strip() if value else None

    return _configured_value(provider, "model")

def get_provider_runtime_config(
    provider_name: str,
    task: str = "default",
) -> ProviderRuntimeConfig:
    provider = get_provider_config(provider_name)

    if not provider:
        raise RuntimeError(f"Provider '{provider_name}' is not configured.")

    kind = str(provider.get("kind", provider_name)).strip().lower()
    enabled = bool(provider.get("enabled", True))

    model = get_task_model(provider_name, task) or _configured_value(provider, "model")
    if not model:
        raise RuntimeError(f"Provider '{provider_name}' has no model configured.")

    return ProviderRuntimeConfig(
        name=provider_name,
        kind=kind,
        enabled=enabled,
        model=model,
        base_url=_configured_value(provider, "base_url"),
        api_key=get_provider_api_key(provider_name),
        region=_configured_value(provider, "region"),
    )
