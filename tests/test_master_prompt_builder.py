from mirror.generation.master_prompt_builder import build_master_prompt


def test_master_prompt_contains_core_sections():
    prompt = build_master_prompt(
        learner_name="Ana",
        topic="present simple",
        teacher_prompt="Use controlled practice and short corrections.",
        reference_excerpt="Worksheet type: Grammar Worksheet",
    )

    assert "GOAL" in prompt
    assert "USEFUL CONTEXT" in prompt
    assert "TEACHER GUIDANCE" in prompt
    assert "INSTRUCTIONAL METHOD" in prompt
    assert "Ana" in prompt
    assert "present simple" in prompt
