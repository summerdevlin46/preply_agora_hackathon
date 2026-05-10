.PHONY: help \
	lock sync sync-all sync-dev sync-apple-local update clean test \
	env-create env-check \
	deps-check deps-install deps-uninstall setup setup-apple \
	run run-dev run-share \
	local-oss-serve local-oss-serve-tiny local-oss-serve-tinyllama \
	docker-build docker-run docker-run-dev docker-shell

APP_NAME := mirror-app
APP_PORT := 8000
DEV_PORT := 7699
ENV_FILE := .env

help:
	@echo "Available targets:"
	@echo "  make lock                  - Generate/update uv.lock"
	@echo "  make sync                  - Sync base dependencies"
	@echo "  make install_lean          - Lock and sync base dependencies"
	@echo "  make install_all           - Lock and sync all dependency groups"
	@echo "  make sync-all              - Sync all dependency groups"
	@echo "  make sync-dev              - Sync base + dev group"
	@echo "  make sync-apple-local      - Sync all groups including Apple local deps"
	@echo "  make update                - Update lockfile and sync all groups"
	@echo "  make clean                 - Remove caches"
	@echo "  make test                  - Run tests"
	@echo "  make env-create            - Create .env from .env.example"
	@echo "  make env-check             - Check that .env exists"
	@echo "  make deps-check            - Check host OCR system dependencies"
	@echo "  make deps-install          - Install host OCR system dependencies"
	@echo "  make deps-uninstall        - Remove host OCR system dependencies"
	@echo "  make setup                 - Install host deps + all Python deps"
	@echo "  make setup-apple           - Same as setup, including apple_local via all-groups"
	@echo "  make run                   - Run the app on default port ($(APP_PORT))"
	@echo "  make run-dev               - Run the app on dev port ($(DEV_PORT))"
	@echo "  make run-share             - Run the app with Gradio share enabled"
	@echo "  make local-oss-serve       - Run local OSS server with SmolLM2-360M"
	@echo "  make local-oss-serve-tiny  - Run local OSS server with SmolLM2-135M"
	@echo "  make local-oss-serve-tinyllama - Run local OSS server with TinyLlama 1.1B"
	@echo "  make docker-build          - Build the Docker image"
	@echo "  make docker-run            - Run the Docker image with .env"
	@echo "  make docker-run-dev        - Run the Docker image interactively with .env"
	@echo "  make docker-shell          - Open a shell inside the Docker image"

lock:
	uv lock

sync:
	uv sync

install_lean: lock sync

install_all: lock sync-all

sync-all:
	uv sync --all-groups

sync-dev:
	uv sync --group dev

# Keep this as an alias so it does not prune other groups.
sync-apple-local:
	uv sync --all-groups

update:
	uv lock --upgrade
	uv sync --all-groups

clean:
	rm -rf .pytest_cache .ruff_cache .venv __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

test:
	uv run pytest

env-create:
	cp .env.example .env && echo ".env created. Fill in secrets."

env-check:
	@test -f $(ENV_FILE) || (echo ".env file not found. Copy from .env.example"; exit 1)

deps-check:
	./scripts/system_deps.sh check

deps-install:
	./scripts/system_deps.sh install

deps-uninstall:
	./scripts/system_deps.sh uninstall

setup: deps-install sync-all

setup-apple: deps-install sync-all

run: env-check
	uv run python src/app.py --port $(APP_PORT)

run-dev: env-check
	uv run python src/app.py --port $(DEV_PORT)

run-share: env-check
	uv run python src/app.py --port $(APP_PORT) --share

local-oss-serve:
	uv run python -m mlx_lm server --model HuggingFaceTB/SmolLM2-360M-Instruct --host 127.0.0.1 --port 8081

local-oss-serve-tiny:
	uv run python -m mlx_lm server --model HuggingFaceTB/SmolLM2-135M-Instruct --host 127.0.0.1 --port 8081

local-oss-serve-tinyllama:
	uv run python -m mlx_lm server --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --host 127.0.0.1 --port 8081

docker-build:
	docker build -t $(APP_NAME) .

docker-run: env-check
	docker run --rm \
		--env-file $(ENV_FILE) \
		-p $(APP_PORT):$(APP_PORT) \
		$(APP_NAME)

docker-run-dev: env-check
	docker run --rm -it \
		--env-file $(ENV_FILE) \
		-p $(APP_PORT):$(APP_PORT) \
		$(APP_NAME)

docker-shell:
	docker run --rm -it --entrypoint /bin/bash $(APP_NAME)
