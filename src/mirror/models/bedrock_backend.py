"""
AWS Bedrock backend using the Anthropic SDK.

AWS credentials come from the standard chain:
  - Environment variables
  - AWS profile
  - ~/.aws/credentials / ~/.aws/config
  - IAM instance role
"""

import logging
import os
from typing import Optional

import anthropic

from mirror.models.model_config import (
    get_generation_settings,
    get_provider_runtime_config,
)

logger = logging.getLogger(__name__)


def _client(region: str | None = None) -> anthropic.AnthropicBedrock:
    return anthropic.AnthropicBedrock(
        aws_region=region or os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _async_client(region: str | None = None) -> anthropic.AsyncAnthropicBedrock:
    return anthropic.AsyncAnthropicBedrock(
        aws_region=region or os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def generate_text(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    task: str = "default",
) -> str:
    provider = get_provider_runtime_config("bedrock", task=task)
    generation = get_generation_settings(task=task)

    response = _client(region=provider.region).messages.create(
        model=model or provider.model,
        max_tokens=max_tokens or generation.max_tokens,
        temperature=generation.temperature if temperature is None else temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_with_vision(
    prompt: str,
    data_urls: list[str],
    model: Optional[str] = None,
    max_tokens: int | None = None,
    task: str = "ocr_structuring",
) -> str:
    provider = get_provider_runtime_config("bedrock", task=task)
    generation = get_generation_settings(task=task)

    content: list[dict] = []

    for url in data_urls:
        header, b64data = url.split(",", 1)
        media_type = header.split(":")[1].split(";")[0]
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64data,
                },
            }
        )

    content.append({"type": "text", "text": prompt})

    response = _client(region=provider.region).messages.create(
        model=model or provider.model,
        max_tokens=max_tokens or generation.max_tokens,
        temperature=generation.temperature,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


async def generate_text_async(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    task: str = "default",
) -> str:
    provider = get_provider_runtime_config("bedrock", task=task)
    generation = get_generation_settings(task=task)

    response = await _async_client(region=provider.region).messages.create(
        model=model or provider.model,
        max_tokens=max_tokens or generation.max_tokens,
        temperature=generation.temperature if temperature is None else temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_with_bedrock(
    prompt: str,
    model: Optional[str] = None,
    task: str = "default",
    system_prompt: str = "You are a helpful assistant.",
) -> str:
    return generate_text(
        system_prompt=system_prompt,
        user_message=prompt,
        model=model,
        task=task,
    )