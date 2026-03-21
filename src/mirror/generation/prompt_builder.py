def build_exercise_prompt(
    learner_name: str,
    topic: str,
    teacher_prompt: str,
    reference_excerpt: str,
    style_summary: str,
) -> str:
    teacher_notes_block = teacher_prompt.strip() or "No extra teacher notes were provided."

    return f"""
You are an expert ESL/EFL teacher and materials designer.

Your task is to create a NEW worksheet-style exercise for the learner named {learner_name}.

You must use the reference material only as inspiration for:
- difficulty
- task style
- tone
- pedagogical structure

You must NOT:
- copy the worksheet verbatim
- reuse the same sentences
- repeat the same examples
- mention that you used a reference worksheet
- output explanations about your reasoning

You must:
- create an exercise on this new target topic: {topic}
- follow the teacher notes carefully
- keep the output teacher-ready and classroom-usable
- include clear instructions
- include 5 to 8 items
- include an answer key
- keep the formatting neat and easy to read

Teacher notes / pedagogical guidance:
{teacher_notes_block}

Style summary:
{style_summary}

Reference worksheet excerpt:
{reference_excerpt}

Output format:
Title: <short title>

Instructions:
<clear instructions>

Exercise:
1. ...
2. ...
3. ...

Answer Key:
1. ...
2. ...
3. ...

Here is a good example of the kind of output format and quality expected:

Example topic: Past Simple
Example teacher notes: Make it A2 level, controlled practice, with 5 gap-fill items.

Example output:
Title: Past Simple Practice

Instructions:
Complete the sentences with the correct past simple form of the verb in brackets.

Exercise:
1. Yesterday, I ________ (visit) my grandmother.
2. She ________ (not like) the film last night.
3. We ________ (play) football after school.
4. He ________ (study) for the test yesterday evening.
5. They ________ (go) to the museum on Saturday.

Answer Key:
1. visited
2. did not like
3. played
4. studied
5. went

Now generate the real exercise for this request.
""".strip()
