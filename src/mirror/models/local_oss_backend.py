import os

from openai import OpenAI

from mirror.config import get_env


def generate_with_local_oss(prompt: str, model: str | None = None) -> str:
    base_url = get_env("LOCAL_OSS_BASE_URL", "http://127.0.0.1:8081/v1")
    selected_model = model or os.getenv(
        "LOCAL_OSS_MODEL",
        "HuggingFaceTB/SmolLM2-360M-Instruct",
    )

    client = OpenAI(
        base_url=base_url,
        api_key="local-not-used",
    )

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
