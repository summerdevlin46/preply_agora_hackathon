"""
tests/test_generation.py
"""
import pytest
from unittest.mock import patch, MagicMock

from mirror.generation.prompt_builder import build_avatar_system_prompt
from mirror.generation.cleanup import build_cleanup_user_message


# --- prompt_builder tests (no API calls, pure functions) ---

def test_avatar_prompt_contains_all_sections():
    prompt = build_avatar_system_prompt(
        goal_block="Guide the student through 8 sentences.",
        context_block="Focus on missing 'be' verbs.",
    )
    for section in ["PERSONALITY", "ENVIRONMENT", "TONE", "GOAL", "USEFUL CONTEXT", "GUARDRAILS"]:
        assert section in prompt, f"Missing section: {section}"


def test_avatar_prompt_default_avatar_name():
    prompt = build_avatar_system_prompt(
        goal_block="Guide the student through 8 sentences.",
        context_block="Focus on missing 'be' verbs.",
    )
    assert "Leo" in prompt


def test_avatar_prompt_custom_avatar_name():
    prompt = build_avatar_system_prompt(
        goal_block="Guide the student through 8 sentences.",
        context_block="Focus on missing 'be' verbs.",
        avatar_name="Maya",
    )
    assert "Maya" in prompt
    assert "Leo" not in prompt


def test_avatar_prompt_injects_goal():
    goal = "Run a 6-item drill on past simple errors."
    prompt = build_avatar_system_prompt(goal_block=goal, context_block="x")
    assert goal in prompt


def test_avatar_prompt_injects_context():
    context = "Target missing auxiliary verbs only."
    prompt = build_avatar_system_prompt(goal_block="x", context_block=context)
    assert context in prompt


# --- cleanup message builder tests (pure function, no API) ---

def test_cleanup_message_includes_teacher_notes():
    msg = build_cleanup_user_message(
        teacher_notes="Make it A2 level",
        worksheet_json={"topic": "present simple"},
    )
    assert "A2 level" in msg


def test_cleanup_message_includes_feedback_when_provided():
    msg = build_cleanup_user_message(
        teacher_notes="Make it A2 level",
        worksheet_json={},
        feedback="Too easy, increase difficulty",
    )
    assert "Too easy" in msg
    assert "TEACHER FEEDBACK" in msg


def test_cleanup_message_no_feedback_by_default():
    msg = build_cleanup_user_message(
        teacher_notes="notes",
        worksheet_json={},
    )
    assert "TEACHER FEEDBACK" not in msg


# --- workflow integration test (mocked API) ---

@pytest.mark.skip(reason="requires OPENAI_API_KEY")
def test_run_prompt_workflow_end_to_end():
    from mirror.agents.exercise_workflow import run_prompt_workflow
    prompt, error = run_prompt_workflow(
        teacher_notes="Present continuous errors, A2 level, 8 sentences",
        worksheet_json={"topic": "present continuous", "sections": []},
    )
    assert not error
    assert "GOAL" in prompt
