from pathlib import Path

import pytest

from mirror.ocr.file_types import is_pdf, is_supported_image, validate_uploaded_file


def test_validate_uploaded_file_raises_on_none():
    with pytest.raises(ValueError, match="No file was uploaded"):
        validate_uploaded_file(None)


def test_validate_uploaded_file_raises_on_missing_path():
    with pytest.raises(FileNotFoundError):
        validate_uploaded_file("/tmp/definitely_missing_file_12345.pdf")


def test_validate_uploaded_file_returns_path(tmp_path: Path):
    file_path = tmp_path / "worksheet.pdf"
    file_path.write_text("dummy")
    result = validate_uploaded_file(str(file_path))
    assert result == file_path


def test_is_pdf():
    assert is_pdf(Path("lesson.pdf")) is True
    assert is_pdf(Path("lesson.png")) is False


def test_is_supported_image():
    assert is_supported_image(Path("scan.png")) is True
    assert is_supported_image(Path("scan.jpg")) is True
    assert is_supported_image(Path("scan.txt")) is False