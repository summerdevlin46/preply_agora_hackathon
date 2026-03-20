.PHONY: help lock sync sync-all sync-dev update clean test run deps-check deps-install deps-uninstall setup

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
	@echo "  make run             - Run the app"
	@echo "  make deps-check      - Check host OCR system dependencies"
	@echo "  make deps-install    - Install host OCR system dependencies"
	@echo "  make deps-uninstall  - Remove host OCR system dependencies"
	@echo "  make setup           - Install host deps + all Python deps"

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
	uv run python src/app.py

#TODO: run dev is kinda redundant or overlapping with run, run-share is good but may need to be run main
run-dev:
	uv run python src/app.py --port 7699

run-share:
	uv run python src/app.py --port 7860 --share
