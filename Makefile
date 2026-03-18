.PHONY: help lock sync sync-all sync-dev update clean test run

help:
	@echo "Available targets:"
	@echo "  make lock       - Generate/update uv.lock"
	@echo "  make sync       - Sync base dependencies"
	@echo "  make install_lean    - Lock and sync base dependencies"
	@echo "  make install_all    - Lock and sync all dependencies"
	@echo "  make sync-all   - Sync all dependency groups"
	@echo "  make sync-dev   - Sync base + dev group"
	@echo "  make update     - Update lockfile and sync all groups"
	@echo "  make clean      - Remove caches"
	@echo "  make test       - Run tests"
	@echo "  make run        - Run the app module"

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

run:
	uv run python -m preply_hackathon
