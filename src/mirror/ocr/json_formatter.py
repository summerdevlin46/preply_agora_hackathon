from typing import Any


def worksheet_json_to_preview(data: dict[str, Any]) -> str:
    parts: list[str] = []

    title = data.get("title") or "Untitled Worksheet"
    parts.append(f"Title: {title}")

    worksheet_type = data.get("worksheet_type", "unknown")
    level = data.get("level", "unknown")
    topic = data.get("topic", "unknown")
    parts.append(f"Type: {worksheet_type}")
    parts.append(f"Level: {level}")
    parts.append(f"Topic: {topic}")
    parts.append("")

    instructions = data.get("instructions", [])
    if instructions:
        parts.append("Instructions:")
        for item in instructions:
            parts.append(f"- {item}")
        parts.append("")

    sections = data.get("sections", [])
    for idx, section in enumerate(sections, start=1):
        heading = section.get("heading") or f"Section {idx}"
        task_type = section.get("task_type") or "unknown"
        parts.append(f"{heading} ({task_type})")

        for inst in section.get("instructions", []):
            parts.append(f"- {inst}")

        for item in section.get("items", []):
            parts.append(f"  • {item}")

        examples = section.get("examples", [])
        if examples:
            parts.append("  Examples:")
            for ex in examples:
                parts.append(f"    - {ex}")

        parts.append("")

    answer_key = data.get("answer_key", [])
    if answer_key:
        parts.append("Answer Key:")
        for item in answer_key:
            parts.append(f"- {item}")
        parts.append("")

    notes = data.get("notes", [])
    if notes:
        parts.append("Notes:")
        for note in notes:
            parts.append(f"- {note}")
        parts.append("")

    raw_text = data.get("raw_text", "").strip()
    if raw_text:
        parts.append("Raw Text:")
        parts.append(raw_text)

    return "\n".join(parts).strip()
