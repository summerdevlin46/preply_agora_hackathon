from mirror.generation.prompt_builder import build_exercise_prompt


def test_generation_prompt_flow_includes_reference_and_constraints():
    prompt = build_exercise_prompt(
        learner_name="Ana",
        topic="present simple",
        teacher_prompt=(
            "Make it A2, controlled practice, 5 gap-fill items and one short speaking follow-up."
        ),
        reference_excerpt=(
            "Worksheet type: Grammar Worksheet\n"
            "Level: unknown\n"
            "Topic: Adverbs of Frequency\n\n"
            "Instructions:\n"
            "- Study the adverbs of frequency in the table below.\n"
        ),
        style_summary="grammar worksheet, guided practice, sentence completion, beginner-friendly",
    )

    assert "Ana" in prompt
    assert "present simple" in prompt
    assert "Adverbs of Frequency" in prompt
    assert "5 gap-fill items" in prompt
    assert "Output format:" in prompt
    assert "Example output:" in prompt
    assert "do not copy" in prompt.lower()
