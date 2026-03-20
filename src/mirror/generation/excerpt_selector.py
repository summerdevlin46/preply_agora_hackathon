import re


def select_reference_excerpt(worksheet_text: str, max_chars: int = 1800) -> str:
    """
    Pick the most instruction-rich parts of the worksheet while staying
    within a prompt budget.
    """
    if not worksheet_text.strip():
        return ""

    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", worksheet_text) if chunk.strip()]

    def score(chunk: str) -> int:
        lowered = chunk.lower()
        points = 0

        keywords = ["instruction", "complete", "fill", "rewrite", "choose", "match", "answer"]
        for kw in keywords:
            if kw in lowered:
                points += 3

        if "____" in chunk:
            points += 4

        if re.search(r"\b\d+[\).\s]", chunk):
            points += 2

        if len(chunk) < 40:
            points -= 1

        return points

    ranked = sorted(chunks, key=score, reverse=True)

    selected = []
    total = 0

    for chunk in ranked:
        if total + len(chunk) > max_chars:
            continue
        selected.append(chunk)
        total += len(chunk) + 2
        if total >= max_chars:
            break

    if not selected:
        return worksheet_text[:max_chars].strip()

    return "\n\n".join(selected).strip()
