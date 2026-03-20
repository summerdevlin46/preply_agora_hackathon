#selected_model = model or os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
import logging
import os

from huggingface_hub import InferenceClient
from huggingface_hub.errors import BadRequestError

from mirror.config import get_env

logger = logging.getLogger(__name__)


def generate_with_huggingface(prompt: str, model: str | None = None) -> str:
    token = get_env("HF_TOKEN")

    env_model = os.getenv("HF_MODEL", "").strip()
    selected_model = (model or env_model or None)

    client = InferenceClient(api_key=token)

    messages = [
        {"role": "system", "content": "You are an expert language tutor."},
        {"role": "user", "content": prompt},
    ]

    try:
        kwargs = {
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.2,
        }

        if selected_model:
            kwargs["model"] = selected_model
            logger.info("Using Hugging Face model: %s", selected_model)
        else:
            logger.info("Using Hugging Face recommended default chat model")

        completion = client.chat.completions.create(**kwargs)
        return completion.choices[0].message.content

    except BadRequestError as exc:
        error_text = str(exc)

        if selected_model and "model_not_supported" in error_text:
            logger.warning(
                "HF model '%s' is not supported by enabled providers. Retrying without explicit model.",
                selected_model,
            )

            completion = client.chat.completions.create(
                messages=messages,
                max_tokens=300,
                temperature=0.2,
            )
            return completion.choices[0].message.content

        raise
