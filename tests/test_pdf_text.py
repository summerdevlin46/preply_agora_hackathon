from mirror.ocr.pdf_text import looks_like_useful_text


def test_looks_like_useful_text_false_for_empty():
    assert looks_like_useful_text("") is False


def test_looks_like_useful_text_false_for_whitespace():
    assert looks_like_useful_text("   \n\t  ") is False


def test_looks_like_useful_text_false_for_too_short_text():
    assert looks_like_useful_text("abc def", min_chars=20) is False


def test_looks_like_useful_text_true_for_real_text():
    text = "This is a real worksheet sentence with enough characters."
    assert looks_like_useful_text(text) is True