from typing import Any


def build_reference_block(data: dict[str, Any]) -> str:
    parts: list[str] = []

    parts.append(f"Worksheet type: {data.get('worksheet_type', 'unknown')}")
    parts.append(f"Level: {data.get('level', 'unknown')}")
    parts.append(f"Topic: {data.get('topic', 'unknown')}")
    parts.append("")

    instructions = data.get("instructions", [])
    if instructions:
        parts.append("Instructions:")
        for inst in instructions[:5]:
            parts.append(f"- {inst}")
        parts.append("")

    sections = data.get("sections", [])

    for section in sections[:2]:  # keep it tight
        parts.append(f"Section: {section.get('heading', 'unknown')}")
        parts.append(f"Task type: {section.get('task_type', 'unknown')}")

        for inst in section.get("instructions", [])[:2]:
            parts.append(f"- {inst}")

        items = section.get("items", [])[:5]
        if items:
            parts.append("Examples:")
            for item in items:
                parts.append(f"- {item}")

        parts.append("")

    return "\n".join(parts).strip()