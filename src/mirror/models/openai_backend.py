import os

from openai import OpenAI

from mirror.config import get_env


def generate_with_openai(prompt: str, model: str | None = None) -> str:
    api_key = get_env("OPENAI_API_KEY")
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5")

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=selected_model,
        input=prompt,
    )
    return response.output_text
