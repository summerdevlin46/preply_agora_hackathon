import os

from openai import OpenAI


def generate_exercise_text(prompt: str, model: str = "gpt-5") -> str:
    """
    Generate the final exercise text from a prepared prompt.
    Falls back to returning the prompt if no API key is configured.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "OPENAI_API_KEY is not set.\n\n"
            "Prompt preview:\n\n"
            f"{prompt}"
        )

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text
