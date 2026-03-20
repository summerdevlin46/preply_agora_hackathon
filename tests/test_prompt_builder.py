from mirror.generation.prompt_builder import build_exercise_prompt


def test_build_exercise_prompt_includes_teacher_notes():
    prompt = build_exercise_prompt(
        learner_name="Ana",
        topic="past simple",
        teacher_prompt="Make it A2 and communicative.",
        reference_excerpt="Complete the sentences...",
        style_summary="fill-in-the-blank, beginner-friendly",
    )

    assert "Make it A2 and communicative." in prompt
    assert "past simple" in prompt
    assert "Ana" in prompt


def test_build_exercise_prompt_handles_empty_teacher_notes():
    prompt = build_exercise_prompt(
        learner_name="Ana",
        topic="past simple",
        teacher_prompt="",
        reference_excerpt="Complete the sentences...",
        style_summary="fill-in-the-blank",
    )

    assert "No extra teacher notes were provided." in prompt
    assert "past simple" in prompt


def test_build_exercise_prompt_includes_reference_excerpt():
    prompt = build_exercise_prompt(
        learner_name="Luis",
        topic="frequency adverbs",
        teacher_prompt="Use controlled practice.",
        reference_excerpt="Worksheet type: Grammar Worksheet",
        style_summary="sentence completion",
    )

    assert "Worksheet type: Grammar Worksheet" in prompt
    assert "sentence completion" in prompt


def test_build_exercise_prompt_includes_output_format_and_example():
    prompt = build_exercise_prompt(
        learner_name="Mia",
        topic="present continuous",
        teacher_prompt="Make it simple.",
        reference_excerpt="Some reference text",
        style_summary="guided grammar practice",
    )

    assert "Output format:" in prompt
    assert "Example output:" in prompt
    assert "Answer Key:" in prompt
