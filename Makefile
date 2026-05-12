.PHONY: help \
	lock sync sync-dev sync-apple-local sync-audio update clean test \
	env-check \
	run-api run-model run-model-tiny run-model-qwen \
	docker-build docker-run docker-shell

APP_NAME := afterclass-api
APP_HOST := 127.0.0.1
APP_PORT := 8000
ENV_FILE := .env

LOCAL_OSS_HOST := 127.0.0.1
LOCAL_OSS_PORT := 8081
LOCAL_OSS_MODEL := HuggingFaceTB/SmolLM2-360M-Instruct

help:
	@echo "Available targets:"
	@echo "  make lock              - Generate/update uv.lock"
	@echo "  make sync              - Sync base runtime dependencies"
	@echo "  make sync-dev          - Sync dev dependencies"
	@echo "  make sync-apple-local  - Sync Apple Silicon local model dependencies"
	@echo "  make sync-audio        - Sync optional audio dependencies"
	@echo "  make update            - Upgrade lockfile and sync base dependencies"
	@echo "  make clean             - Remove caches"
	@echo "  make test              - Run tests"
	@echo "  make env-check         - Check that .env exists"
	@echo "  make run-api           - Run FastAPI backend on $(APP_HOST):$(APP_PORT)"
	@echo "  make run-model         - Run local OpenAI-compatible MLX server"
	@echo "  make run-model-tiny    - Run smaller SmolLM2 local model"
	@echo "  make run-model-qwen    - Run stronger Qwen local model"
	@echo "  make docker-build      - Build backend Docker image"
	@echo "  make docker-run        - Run backend Docker image"
	@echo "  make docker-shell      - Open shell in backend Docker image"

lock:
	uv lock

sync:
	uv sync

sync-dev:
	uv sync --group dev

sync-apple-local:
	uv sync --group apple_local

sync-audio:
	uv sync --group audio

update:
	uv lock --upgrade
	uv sync

clean:
	rm -rf .pytest_cache .ruff_cache .venv __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

test:
	uv run pytest

env-check:
	@test -f $(ENV_FILE) || (echo ".env file not found. Copy from .env.example"; exit 1)

run-api: env-check
	uv run python src/app.py --host $(APP_HOST) --port $(APP_PORT) --reload

run-model:
	uv run python -m mlx_lm server \
		--model $(LOCAL_OSS_MODEL) \
		--host $(LOCAL_OSS_HOST) \
		--port $(LOCAL_OSS_PORT)

run-model-tiny:
	$(MAKE) run-model LOCAL_OSS_MODEL=HuggingFaceTB/SmolLM2-135M-Instruct

run-model-qwen:
	$(MAKE) run-model LOCAL_OSS_MODEL=Qwen/Qwen3-4B-Instruct-2507

docker-build:
	docker build -t $(APP_NAME) .

docker-run: env-check
	docker run --rm \
		--env-file $(ENV_FILE) \
		-e APP_HOST=0.0.0.0 \
		-e APP_PORT=$(APP_PORT) \
		-p $(APP_PORT):$(APP_PORT) \
		$(APP_NAME)

docker-shell:
	docker run --rm -it --entrypoint /bin/bash $(APP_NAME)
