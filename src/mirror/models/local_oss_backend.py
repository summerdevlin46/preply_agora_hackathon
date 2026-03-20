import logging
import os

from openai import APIConnectionError, OpenAI

from mirror.config import get_env

logger = logging.getLogger(__name__)


def generate_with_local_oss(prompt: str, model: str | None = None) -> str:
    base_url = get_env("LOCAL_OSS_BASE_URL", "http://127.0.0.1:8081/v1")
    selected_model = model or os.getenv(
        "LOCAL_OSS_MODEL",
        "HuggingFaceTB/SmolLM2-360M-Instruct",
    )

    logger.info("Using local OSS model: %s", selected_model)

    client = OpenAI(
        base_url=base_url,
        api_key="local-not-used",
    )

    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "You are an expert language tutor."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.2,
        )

        return response.choices[0].message.content

    except APIConnectionError as exc:
        logger.error("Local OSS server unreachable at %s", base_url)
        return (
            "Local model server is not running.\n\n"
            f"Expected at: {base_url}\n\n"
            "Run:\n"
            "uv run python -m mlx_lm server --model HuggingFaceTB/SmolLM2-360M-Instruct\n"
        )