"""
mirror/models/bedrock_backend.py

AWS Bedrock backend using the Anthropic SDK (AnthropicBedrock).
Reads AWS credentials from the standard chain:
  - Environment: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
  - ~/.aws/credentials / ~/.aws/config
  - IAM instance role
"""
import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

BEDROCK_MODEL = os.getenv(
    "BEDROCK_MODEL",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
)


def _client() -> anthropic.AnthropicBedrock:
    return anthropic.AnthropicBedrock(
        aws_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _async_client() -> anthropic.AsyncAnthropicBedrock:
    return anthropic.AsyncAnthropicBedrock(
        aws_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def generate_text(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int = 2500,
) -> str:
    response = _client().messages.create(
        model=model or BEDROCK_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_with_vision(
    prompt: str,
    data_urls: list[str],
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> str:
    """
    Send text + images to Bedrock. data_urls must be standard RFC 2397 data URLs
    ("data:<media_type>;base64,<data>").
    Images are placed before the prompt so the model sees them in context first.
    """
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

    response = _client().messages.create(
        model=model or BEDROCK_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


async def generate_text_async(
    system_prompt: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: int = 2500,
) -> str:
    response = await _async_client().messages.create(
        model=model or BEDROCK_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_with_bedrock(prompt: str, model: Optional[str] = None) -> str:
    """Single-string generation shim for factory.py compatibility."""
    return generate_text(
        system_prompt="You are a helpful assistant.",
        user_message=prompt,
        model=model,
    )
