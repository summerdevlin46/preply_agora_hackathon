FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --all-groups --frozen --no-install-project

COPY src ./src
COPY schema ./schema
COPY config ./config
COPY prompts ./prompts
COPY data ./data

EXPOSE ${APP_PORT}

CMD ["sh", "-c", "uv run python src/app.py --host ${APP_HOST} --port ${APP_PORT}"]
