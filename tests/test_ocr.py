import pytest
from mirror.utils.ocr import parse_worksheet, clean_text


@pytest.mark.skip(reason="OCR not implemented yet")
def test_parse_worksheet_returns_string():
    result = parse_worksheet("fake/path/to/worksheet.pdf")
    assert isinstance(result, str)


@pytest.mark.skip(reason="OCR not implemented yet")
def test_parse_worksheet_empty_file():
    """TODO: decide — should an empty file raise or return an empty string?"""
    raise NotImplementedError


@pytest.mark.skip(reason="not implemented yet")
def test_clean_text_strips_whitespace():
    result = clean_text("  hello   world  ")
    assert result == "hello world"
