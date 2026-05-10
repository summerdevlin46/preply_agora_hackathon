import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationSettings:
    model: str
    max_tokens: int
    temperature: float


def _env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _env_float(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return float(value)


def get_local_oss_settings(task: str = "default") -> GenerationSettings:
    """
    Temporary env-based settings.

    Later this can read YAML first, then let env vars override it.
    The task arg is here now so we can support per-pipeline settings next:
      - default
      - chat
      - exercise
      - report
      - cleanup
      - ocr_structuring
    """
    task_prefix = task.upper()

    model = (
        os.getenv(f"AFTERCLASS_{task_prefix}_LOCAL_OSS_MODEL")
        or os.getenv("AFTERCLASS_LOCAL_OSS_MODEL")
        or "HuggingFaceTB/SmolLM2-360M-Instruct"
    )

    max_tokens = _env_int(
        f"AFTERCLASS_{task_prefix}_LOCAL_OSS_MAX_TOKENS",
        _env_int("AFTERCLASS_LOCAL_OSS_MAX_TOKENS", 1200),
    )

    temperature = _env_float(
        f"AFTERCLASS_{task_prefix}_LOCAL_OSS_TEMPERATURE",
        _env_float("AFTERCLASS_LOCAL_OSS_TEMPERATURE", 0.2),
    )

    return GenerationSettings(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
