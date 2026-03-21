from mirror.ocr.reference_builder import build_reference_block


def test_build_reference_block_includes_core_fields():
    data = {
        "worksheet_type": "Grammar Worksheet",
        "level": "A1",
        "topic": "Frequency Adverbs",
        "instructions": ["Study the table."],
        "sections": [
            {
                "heading": "1 THEORY",
                "task_type": "Table Study",
                "instructions": ["Read the examples."],
                "items": ["Always = 100%", "Usually = 90%"],
                "examples": [],
            }
        ],
    }

    result = build_reference_block(data)

    assert "Worksheet type: Grammar Worksheet" in result
    assert "Level: A1" in result
    assert "Topic: Frequency Adverbs" in result
    assert "Section: 1 THEORY" in result
    assert "Task type: Table Study" in result
