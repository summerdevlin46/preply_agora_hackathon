from mirror.generation.tutor_prompt_builder import build_tutor_prompt


def test_build_tutor_prompt_includes_teacher_notes_and_topic():
    prompt = build_tutor_prompt(
        learner_name="Ana",
        topic="present simple",
        teacher_prompt="Use guided elicitation and short corrective feedback.",
        reference_excerpt="Worksheet type: Grammar Worksheet",
        style_summary="guided grammar practice, beginner-friendly",
    )

    assert "Ana" in prompt
    assert "present simple" in prompt
    assert "Use guided elicitation and short corrective feedback." in prompt
    assert "Speak as a tutor, not as a worksheet." in prompt
