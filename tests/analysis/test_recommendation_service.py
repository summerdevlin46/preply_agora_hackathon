import asyncio
import json

from mirror.analysis import recommendation_service as rec


DEMO_TRANSCRIPT = (
    "Teacher: What are you cooking right now?\n"
    "Student: I am mixing the cake ingredients.\n"
    "Teacher: What is your sister doing?\n"
    "Student: She is bake a cake.\n"
    "Teacher: Good try. Say: she is baking a cake."
)


def test_iter_transcript_turns_handles_inline_transcript():
    transcript = (
        "Teacher: What are you cooking? "
        "Student: I am mixing. "
        "Teacher: What is she doing? "
        "Student: She is bake a cake."
    )

    turns = rec._iter_transcript_turns(transcript)

    assert turns == [
        ("teacher", "Teacher: What are you cooking?"),
        ("student", "Student: I am mixing."),
        ("teacher", "Teacher: What is she doing?"),
        ("student", "Student: She is bake a cake."),
    ]


def test_extract_transcript_signals_detects_present_continuous_issue():
    signals = rec._extract_transcript_signals(DEMO_TRANSCRIPT)

    assert signals.student_turn_count == 2
    assert signals.teacher_turn_count == 3
    assert signals.learner_examples == [
        "Student: I am mixing the cake ingredients.",
        "Student: She is bake a cake.",
    ]
    assert signals.teacher_corrections == [
        "Teacher: Good try. Say: she is baking a cake."
    ]
    assert signals.possible_errors == [
        "Possible present continuous form issue: 'is bake' may need a verb-ing form."
    ]
    assert signals.warnings == []


def test_extract_transcript_signals_warns_when_no_learner_turns():
    transcript = "Teacher: Today we are practicing cooking vocabulary."

    signals = rec._extract_transcript_signals(transcript)

    assert signals.student_turn_count == 0
    assert signals.teacher_turn_count == 1
    assert "No learner turns were detected in the transcript." in signals.warnings


def test_parse_json_extracts_json_object_from_wrapped_model_output():
    raw = """
    Here is the report:

    {
      "error_summary": "The learner used a base verb after is.",
      "strengths": "The learner understood the cooking context.",
      "areas_to_improve": "Practice present continuous forms.",
      "suggested_next_topic": "Present continuous with cooking verbs."
    }
    """

    parsed = rec._parse_json(raw)

    assert parsed["error_summary"] == "The learner used a base verb after is."
    assert parsed["strengths"] == "The learner understood the cooking context."


def test_parse_loose_report_handles_label_style_output():
    raw = """
    Error summary: The learner said she is bake a cake.
    Strengths: The learner answered the teacher's questions.
    Areas to improve: Practice verb-ing after am, is, and are.
    Suggested next topic: Present continuous cooking actions.
    """

    parsed = rec._parse_json(raw)

    assert parsed["error_summary"] == "The learner said she is bake a cake."
    assert parsed["strengths"] == "The learner answered the teacher's questions."
    assert parsed["areas_to_improve"] == "Practice verb-ing after am, is, and are."
    assert parsed["suggested_next_topic"] == "Present continuous cooking actions."


def test_analyze_session_uses_fallback_when_model_is_unavailable(monkeypatch):
    def fake_generate_with_backend(*args, **kwargs):
        raise RuntimeError("local model unavailable")

    monkeypatch.setattr(rec, "generate_with_backend", fake_generate_with_backend)

    report = asyncio.run(
        rec.analyze_session(
            chat_id="rec-demo",
            transcript=DEMO_TRANSCRIPT,
        )
    )

    assert report.chat_id == "rec-demo"
    assert "is bake" in report.error_summary
    assert "present continuous" in report.areas_to_improve.lower()
    assert "model_call_failed" in report.raw_recommendations["fallback_reason"]
    assert report.raw_recommendations["transcript_signals"]["student_turn_count"] == 2


def test_analyze_session_keeps_valid_model_output(monkeypatch):
    def fake_generate_with_backend(*args, **kwargs):
        return json.dumps(
            {
                "error_summary": "The learner used 'is bake' instead of 'is baking'.",
                "strengths": "The learner used relevant cooking vocabulary.",
                "areas_to_improve": "Practice verb-ing after is.",
                "suggested_next_topic": "Present continuous for cooking actions.",
            }
        )

    monkeypatch.setattr(rec, "generate_with_backend", fake_generate_with_backend)

    report = asyncio.run(
        rec.analyze_session(
            chat_id="rec-demo",
            transcript=DEMO_TRANSCRIPT,
        )
    )

    assert report.error_summary == "The learner used 'is bake' instead of 'is baking'."
    assert report.strengths == "The learner used relevant cooking vocabulary."
    assert report.areas_to_improve == "Practice verb-ing after is."
    assert report.suggested_next_topic == "Present continuous for cooking actions."
    assert "fallback_reason" not in report.raw_recommendations


def test_analyze_session_completes_incomplete_model_output(monkeypatch):
    def fake_generate_with_backend(*args, **kwargs):
        return json.dumps(
            {
                "strengths": "The learner used relevant cooking vocabulary."
            }
        )

    monkeypatch.setattr(rec, "generate_with_backend", fake_generate_with_backend)

    report = asyncio.run(
        rec.analyze_session(
            chat_id="rec-demo",
            transcript=DEMO_TRANSCRIPT,
        )
    )

    assert report.strengths == "The learner used relevant cooking vocabulary."
    assert "is bake" in report.error_summary
    assert "present continuous" in report.areas_to_improve.lower()
    assert report.raw_recommendations["fallback_reason"] == "incomplete_model_output"
    assert set(report.raw_recommendations["fallback_used_for_fields"]) == {
        "error_summary",
        "areas_to_improve",
        "suggested_next_topic",
    }
