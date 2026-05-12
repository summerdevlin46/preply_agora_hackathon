def preview_text(value: str, max_chars: int = 2000) -> str:
    text = value.strip()

    if len(text) <= max_chars:
        return text

    omitted = len(text) - max_chars
    return f"{text[:max_chars]}\n\n...[truncated {omitted} chars]"
