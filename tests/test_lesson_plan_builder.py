from mirror.generation.lesson_plan_builder import build_lesson_plan


def test_build_lesson_plan_returns_both_prompts():
    plan = build_lesson_plan(
        learner_name="Ana",
        topic="present simple",
        teacher_prompt="Use guided elicitation and short corrective feedback.",
        reference_excerpt="Worksheet type: Grammar Worksheet\nTopic: Adverbs of Frequency",
        style_summary="guided grammar practice, beginner-friendly",
    )

    assert "tutor_prompt" in plan
    assert "exercise_prompt" in plan

    assert "Ana" in plan["tutor_prompt"]
    assert "present simple" in plan["tutor_prompt"]

    assert "Ana" in plan["exercise_prompt"]
    assert "present simple" in plan["exercise_prompt"]


def test_tutor_and_exercise_prompts_have_different_intents():
    plan = build_lesson_plan(
        learner_name="Luis",
        topic="present continuous",
        teacher_prompt="Be supportive and keep turns short.",
        reference_excerpt="Worksheet type: Grammar Worksheet",
        style_summary="beginner-friendly grammar practice",
    )

    assert "Speak as a tutor, not as a worksheet." in plan["tutor_prompt"]
    assert "follow-up practice exercise" in plan["exercise_prompt"]
