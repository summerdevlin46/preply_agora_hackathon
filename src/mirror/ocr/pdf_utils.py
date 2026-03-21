import base64
from pathlib import Path
from pdf2image import convert_from_path


def image_file_to_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix == "jpg":
        suffix = "jpeg"

    mime = f"image/{suffix}"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def pdf_to_page_data_urls(path: Path) -> list[str]:
    """
    Convert each PDF page to an in-memory image and return data URLs.
    """
    pages = convert_from_path(str(path))
    data_urls: list[str] = []

    for page in pages:
        import io

        buffer = io.BytesIO()
        page.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data_urls.append(f"data:image/png;base64,{encoded}")

    return data_urls
