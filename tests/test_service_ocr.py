from pathlib import Path
from unittest.mock import patch

import pytest

from mirror.ocr import parse_worksheet


def test_parse_worksheet_uses_pdf_extraction_when_text_is_useful(tmp_path: Path):
    file_path = tmp_path / "worksheet.pdf"
    file_path.write_text("dummy")

    with patch("mirror.ocr.parser.extract_text_from_pdf", return_value="useful extracted text"), \
         patch("mirror.ocr.parser.looks_like_useful_text", return_value=True), \
         patch("mirror.ocr.parser.clean_text", return_value="cleaned text"), \
         patch("mirror.ocr.parser.ocr_pdf") as mock_ocr_pdf:

        result = parse_worksheet(str(file_path))

    assert result == "cleaned text"
    mock_ocr_pdf.assert_not_called()


def test_parse_worksheet_falls_back_to_pdf_ocr_when_text_is_not_useful(tmp_path: Path):
    file_path = tmp_path / "worksheet.pdf"
    file_path.write_text("dummy")

    with patch("mirror.ocr.parser.extract_text_from_pdf", return_value=""), \
         patch("mirror.ocr.parser.looks_like_useful_text", return_value=False), \
         patch("mirror.ocr.parser.ocr_pdf", return_value="ocr text"), \
         patch("mirror.ocr.parser.clean_text", return_value="cleaned ocr text"):

        result = parse_worksheet(str(file_path))

    assert result == "cleaned ocr text"


def test_parse_worksheet_uses_image_ocr_for_images(tmp_path: Path):
    file_path = tmp_path / "worksheet.png"
    file_path.write_text("dummy")

    with patch("mirror.ocr.parser.ocr_image", return_value="image text"), \
         patch("mirror.ocr.parser.clean_text", return_value="cleaned image text"):

        result = parse_worksheet(str(file_path))

    assert result == "cleaned image text"


def test_parse_worksheet_rejects_unsupported_file_type(tmp_path: Path):
    file_path = tmp_path / "worksheet.txt"
    file_path.write_text("dummy")

    result = parse_worksheet(str(file_path))
    assert "Unsupported file type" in result
