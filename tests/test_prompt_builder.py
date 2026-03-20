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


def test_build_exercise_prompt_handles_empty_teacher_notes():
    prompt = build_exercise_prompt(
        learner_name="Ana",
        topic="past simple",
        teacher_prompt="",
        reference_excerpt="Complete the sentences...",
        style_summary="fill-in-the-blank",
    )

    assert "past simple" in prompt
    assert "No extra teacher notes" in prompt
