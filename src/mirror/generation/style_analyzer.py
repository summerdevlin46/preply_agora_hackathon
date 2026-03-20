import re

def analyze_style(worksheet_text: str) -> str:
    """
    Return a small human-readable summary of the worksheet style.
    This is heuristic for now; later it can become an LLM step.
    """
    text = worksheet_text.lower()

    if "____" in worksheet_text:
        exercise_type = "fill-in-the-blank"
    elif re.search(r"\b(a\)|b\)|c\)|d\))", text):
        exercise_type = "multiple choice"
    elif "rewrite" in text or "transform" in text:
        exercise_type = "sentence transformation"
    elif "match" in text:
        exercise_type = "matching"
    else:
        exercise_type = "short-answer practice"

    difficulty = "beginner-friendly"
    if len(worksheet_text) > 3000:
        difficulty = "moderate difficulty"

    return (
        f"Exercise type appears to be {exercise_type}. "
        f"The overall difficulty seems {difficulty}. "
        "Keep the output teacher-ready and concise."
    )
