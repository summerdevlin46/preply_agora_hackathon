FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for OCR / PDF conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies from lockfile
RUN uv sync --all-groups --frozen --no-install-project

# Copy application source
COPY src ./src
COPY tests ./tests
COPY Makefile ./

EXPOSE 7860

CMD ["uv", "run", "python", "src/app.py", "--port", "7860"]
