"""
tests/test_generation.py
"""
import pytest
from unittest.mock import patch, MagicMock

from mirror.generation.prompt_builder import get_avatar_prompt
from mirror.generation.cleanup import (
    build_cleanup_user_message,
    MODES,
    run_cleanup,
)


def test_modes_contains_all_four():
    assert set(MODES) == {
        "avatar_conversation",
        "vocabulary_challenge",
        "read_aloud_review",
        "error_detective",
    }


def test_get_avatar_prompt_returns_correct_mode():
    prompts = {m: f"prompt for {m}" for m in MODES}
    assert get_avatar_prompt(prompts, "error_detective") == "prompt for error_detective"


def test_get_avatar_prompt_raises_on_unknown_mode():
    prompts = {m: f"prompt for {m}" for m in MODES}
    with pytest.raises(ValueError, match="Unknown mode"):
        get_avatar_prompt(prompts, "nonexistent_mode")


def test_cleanup_message_includes_teacher_notes():
    msg = build_cleanup_user_message(
        teacher_notes="B1 level, cooking vocabulary",
        worksheet_json={"topic": "present continuous"},
    )
    assert "B1 level" in msg


def test_cleanup_message_includes_feedback_when_provided():
    msg = build_cleanup_user_message(
        teacher_notes="notes",
        worksheet_json={},
        feedback="Make error_detective harder",
        mode="error_detective",
    )
    assert "Make error_detective harder" in msg
    assert "TEACHER FEEDBACK" in msg


def test_cleanup_message_no_feedback_block_by_default():
    msg = build_cleanup_user_message(
        teacher_notes="notes",
        worksheet_json={},
    )
    assert "TEACHER FEEDBACK" not in msg


def _mock_response(prompts, tasks):
    import json
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps({**prompts, "tasks": tasks})
    return mock


def _valid_prompts():
    return {m: f"You are an avatar for {m}." for m in MODES}


def _valid_tasks():
    return {
        m: [
            {"title": "Step One", "description": "Do the first thing."},
            {"title": "Step Two", "description": "Do the second thing."},
            {"title": "Wrap Up", "description": "Finish the session."},
        ]
        for m in MODES
    }


@patch("mirror.generation.cleanup.OpenAI")
def test_run_cleanup_returns_all_modes(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = (
        _mock_response(_valid_prompts(), _valid_tasks())
    )
    result = run_cleanup(teacher_notes="B1 cooking", worksheet_json={"topic": "x"})
    for mode in MODES:
        assert mode in result
    assert "tasks" in result
    for mode in MODES:
        assert len(result["tasks"][mode]) == 3


@patch("mirror.generation.cleanup.OpenAI")
def test_run_cleanup_tasks_have_title_and_description(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = (
        _mock_response(_valid_prompts(), _valid_tasks())
    )
    result = run_cleanup(teacher_notes="notes", worksheet_json={})
    for mode in MODES:
        for task in result["tasks"][mode]:
            assert "title" in task and task["title"]
            assert "description" in task and task["description"]


@patch("mirror.generation.cleanup.OpenAI")
def test_run_cleanup_raises_on_missing_mode(mock_openai):
    import json
    incomplete = {m: "prompt" for m in MODES if m != "error_detective"}
    incomplete["tasks"] = _valid_tasks()
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(incomplete)
    mock_openai.return_value.chat.completions.create.return_value = mock
    with pytest.raises(RuntimeError, match="missing modes"):
        run_cleanup(teacher_notes="notes", worksheet_json={})


@patch("mirror.generation.cleanup.OpenAI")
def test_run_cleanup_raises_on_wrong_task_count(mock_openai):
    import json
    bad_tasks = _valid_tasks()
    bad_tasks["error_detective"] = [{"title": "Only one", "description": "task"}]
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps({**_valid_prompts(), "tasks": bad_tasks})
    mock_openai.return_value.chat.completions.create.return_value = mock
    with pytest.raises(RuntimeError, match="3 tasks"):
        run_cleanup(teacher_notes="notes", worksheet_json={})


@patch("mirror.generation.cleanup.OpenAI")
def test_run_cleanup_feedback_included_in_message(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = (
        _mock_response(_valid_prompts(), _valid_tasks())
    )
    run_cleanup(
        teacher_notes="B1 cooking",
        worksheet_json={},
        feedback="Make it harder",
        mode="error_detective",
        existing_prompts={m: "existing" for m in MODES},
    )
    call_args = mock_openai.return_value.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    user_msg = next(m["content"] for m in messages if m["role"] == "user")
    assert "Make it harder" in user_msg
    assert "error_detective" in user_msg


@pytest.mark.skip(reason="requires OPENAI_API_KEY")
def test_run_prompt_workflow_end_to_end():
    from mirror.agents.exercise_workflow import run_prompt_workflow
    result, error = run_prompt_workflow(
        teacher_notes="B1 level, present continuous cooking",
        worksheet_json={"topic": "present continuous", "sections": []},
    )
    assert not error
    for mode in MODES:
        assert mode in result
    assert "tasks" in result
