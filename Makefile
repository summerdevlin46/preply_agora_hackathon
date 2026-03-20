.PHONY: help \
	lock sync sync-all sync-dev update clean test \
	deps-check deps-install deps-uninstall setup \
	run run-dev run-share \
	docker-build docker-run docker-run-dev docker-shell

APP_NAME := mirror-app
APP_PORT := 7860
DEV_PORT := 7699

help:
	@echo "Available targets:"
	@echo "  make lock            - Generate/update uv.lock"
	@echo "  make sync            - Sync base dependencies"
	@echo "  make install_lean    - Lock and sync base dependencies"
	@echo "  make install_all     - Lock and sync all dependencies"
	@echo "  make sync-all        - Sync all dependency groups"
	@echo "  make sync-dev        - Sync base + dev group"
	@echo "  make update          - Update lockfile and sync all groups"
	@echo "  make clean           - Remove caches"
	@echo "  make test            - Run tests"
	@echo "  make deps-check      - Check host OCR system dependencies"
	@echo "  make deps-install    - Install host OCR system dependencies"
	@echo "  make deps-uninstall  - Remove host OCR system dependencies"
	@echo "  make setup           - Install host deps + all Python deps"
	@echo "  make run             - Run the app on default port ($(APP_PORT))"
	@echo "  make run-dev         - Run the app on dev port ($(DEV_PORT))"
	@echo "  make run-share       - Run the app with Gradio share enabled"
	@echo "  make docker-build    - Build the Docker image"
	@echo "  make docker-run      - Run the Docker image"
	@echo "  make docker-run-dev  - Run the Docker image interactively"
	@echo "  make docker-shell    - Open a shell inside the Docker image"

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

update:
	uv lock --upgrade
	uv sync --all-groups

clean:
	rm -rf .pytest_cache .ruff_cache .venv __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

test:
	uv run pytest

deps-check:
	./scripts/system_deps.sh check

deps-install:
	./scripts/system_deps.sh install

deps-uninstall:
	./scripts/system_deps.sh uninstall

setup: deps-install sync-all

run:
	uv run python src/app.py --port $(APP_PORT)

run-dev:
	uv run python src/app.py --port $(DEV_PORT)

run-share:
	uv run python src/app.py --port $(APP_PORT) --share

docker-build:
	docker build -t $(APP_NAME) .

docker-run:
	docker run --rm -p $(APP_PORT):$(APP_PORT) $(APP_NAME)

docker-run-dev:
	docker run --rm -it -p $(APP_PORT):$(APP_PORT) $(APP_NAME)

docker-shell:
	docker run --rm -it --entrypoint /bin/bash $(APP_NAME)
