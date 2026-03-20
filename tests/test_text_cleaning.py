from mirror.ocr.text_cleaning import clean_text


def test_clean_text_normalizes_line_endings():
    raw = "hello\r\nworld\rtest"
    assert clean_text(raw) == "hello\nworld\ntest"


def test_clean_text_collapses_extra_spaces():
    raw = "hello     world"
    assert clean_text(raw) == "hello world"


def test_clean_text_collapses_extra_blank_lines():
    raw = "a\n\n\n\nb"
    assert clean_text(raw) == "a\n\nb"


def test_clean_text_strips_edges():
    raw = "   hello world   "
    assert clean_text(raw) == "hello world"