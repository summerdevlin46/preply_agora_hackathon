def verify_generated_exercise(topic: str, generated_text: str) -> str | None:
    """
    Return an error message if the generated text looks obviously wrong.
    Return None if it passes basic checks.
    """
    text = generated_text.strip()

    if not text:
        return "Generation failed: empty output."

    if len(text) < 120:
        return "Generation failed: output is too short."

    if topic.strip().lower() not in text.lower():
        # Soft check; useful for obvious misses
        return (
            f"Generated exercise may not clearly address the requested topic: {topic}"
        )

    return None
