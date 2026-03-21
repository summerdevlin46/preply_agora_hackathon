import os
from openai import OpenAI


def _extract_text(response) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    try:
        return "".join(
            block.text
            for item in response.output
            for block in item.content
            if block.type == "output_text"
        )
    except Exception:
        return str(response)

 ##"gpt-5" FIXING STUFF
def generate_exercise_text(
    prompt: str,
    model: str ="gpt-4o",
    feedback: str | None = None,
) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return f"OPENAI_API_KEY not set.\n\nPrompt:\n{prompt}"

    client = OpenAI()

    if feedback:
        prompt = f"""
You are revising an ESL exercise based on teacher feedback.

IMPORTANT:
- Keep the SAME structure
- Improve clarity and pedagogy

Teacher feedback:
{feedback}

---

{prompt}
"""

    prompt = f"""
{prompt}

=====================
OUTPUT FORMAT (STRICT)
=====================

=== LESSON PLAN ===
Goal: ...
Approach: ...

=== STUDENT TASK ===
Instructions:
...

Exercise:
1. ...
2. ...

=== ANSWER KEY ===
1. ...
2. ...

=== TEACHER NOTES ===
- ...
"""

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=800,
    )

    return _extract_text(response)