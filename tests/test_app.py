import pytest
from app import generate_exercise


def test_generate_exercise_returns_string():
    """Output should always be a string."""
    result = generate_exercise("Alice", "past tense")
    assert isinstance(result, str)


@pytest.mark.skip(reason="placeholder not implemented yet")
def test_generate_exercise_contains_topic():
    """The exercise should mention the topic somewhere."""
    result = generate_exercise("Alice", "past tense")
    assert "past tense" in result.lower()


@pytest.mark.skip(reason="placeholder not implemented yet")
def test_generate_exercise_contains_learner_name():
    """The exercise should be personalised with the learner's name."""
    result = generate_exercise("Alice", "past tense")
    assert "Alice" in result


@pytest.mark.skip(reason="placeholder not implemented yet")
def test_generate_exercise_empty_topic():
    """TODO: decide — should an empty topic raise, or return a generic exercise?"""
    raise NotImplementedError


@pytest.mark.skip(reason="placeholder not implemented yet")
def test_generate_exercise_empty_name():
    """TODO: decide — should an empty name raise, or still work?"""
    raise NotImplementedError
