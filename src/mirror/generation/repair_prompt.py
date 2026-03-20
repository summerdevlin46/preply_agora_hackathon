def build_repair_prompt(
    original_prompt: str,
    topic: str,
    bad_output: str,
    verification_error: str,
) -> str:
    return f"""
You previously generated an exercise that did not pass validation.

Requested topic:
{topic}

Validation issue:
{verification_error}

Original generation prompt:
{original_prompt}

Previous bad output:
{bad_output}

Please produce a corrected exercise that:
- clearly matches the requested topic
- keeps the intended worksheet style
- includes clear instructions
- includes 5 to 8 questions
- includes a short answer key
""".strip()
