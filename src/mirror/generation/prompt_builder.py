#TODO: prompt can be global var passed around, this can be improved
def build_exercise_prompt(
    learner_name: str,
    topic: str,
    teacher_prompt: str,
    reference_excerpt: str,
    style_summary: str,
) -> str:
    teacher_notes_block = teacher_prompt.strip() or "No extra teacher notes were provided."

    return f"""
You are an expert language tutor.

Create a new language exercise for the learner named {learner_name}.

Requirements:
- The new exercise topic must be: {topic}
- Use the reference worksheet only as a guide for tone, structure, difficulty, and exercise style
- Do not copy the worksheet verbatim
- Produce a clean teacher-ready exercise
- Keep the format simple and readable
- Include clear instructions
- Include 5 to 8 questions
- At the end, add a short answer key

Teacher notes / pedagogical guidance:
{teacher_notes_block}

Style summary:
{style_summary}

Reference worksheet excerpt:
{reference_excerpt}
""".strip()
