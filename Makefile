.PHONY: help \
	lock sync sync-dev sync-apple-local sync-audio update clean test \
	env-check \
	run-api run-model run-model-tiny run-model-qwen smoke-api \
	container-info container-build container-run container-shell \
	compose-dev compose-down compose-logs \
	docker-build docker-run docker-shell

APP_NAME := afterclass-api
APP_HOST := 127.0.0.1
APP_PORT := 8000
ENV_FILE := .env

LOCAL_OSS_HOST := 127.0.0.1
LOCAL_OSS_PORT := 8081
LOCAL_OSS_MODEL := HuggingFaceTB/SmolLM2-360M-Instruct

# Auto-pick Docker if available, otherwise Podman.
# Override with:
#   make compose-dev CONTAINER_RUNTIME=podman
#   make compose-dev CONTAINER_RUNTIME=docker
CONTAINER_RUNTIME ?= $(shell if command -v docker >/dev/null 2>&1; then echo docker; else echo podman; fi)
COMPOSE := $(CONTAINER_RUNTIME) compose

# Container-to-host gateway differs between Docker Desktop and Podman.
ifeq ($(CONTAINER_RUNTIME),podman)
	HOST_GATEWAY ?= host.containers.internal
else
	HOST_GATEWAY ?= host.docker.internal
endif

help:
	@echo "Available targets:"
	@echo ""
	@echo "Python / backend:"
	@echo "  make lock                         - Generate/update uv.lock"
	@echo "  make sync                         - Sync base runtime dependencies"
	@echo "  make sync-dev                     - Sync dev dependencies"
	@echo "  make sync-apple-local             - Sync Apple Silicon local model dependencies"
	@echo "  make sync-audio                   - Sync optional audio dependencies"
	@echo "  make update                       - Upgrade lockfile and sync base dependencies"
	@echo "  make clean                        - Remove caches"
	@echo "  make test                         - Run tests"
	@echo "  make env-check                    - Check that .env exists"
	@echo "  make run-api                      - Run FastAPI backend on $(APP_HOST):$(APP_PORT)"
	@echo "  make smoke-api                    - Test FastAPI backend on $(APP_HOST):$(APP_PORT)"
	@echo ""
	@echo "Local model:"
	@echo "  make run-model                    - Run local OpenAI-compatible MLX server"
	@echo "  make run-model-tiny               - Run smaller SmolLM2 local model"
	@echo "  make run-model-qwen               - Run stronger Qwen local model"
	@echo ""
	@echo "Containers:"
	@echo "  make container-info               - Show selected container runtime"
	@echo "  make container-build              - Build backend container image"
	@echo "  make container-run                - Run backend container image"
	@echo "  make container-shell              - Open shell in backend container image"
	@echo "  make compose-dev                  - Run API + frontend using $(CONTAINER_RUNTIME) compose"
	@echo "  make compose-down                 - Stop compose services"
	@echo "  make compose-logs                 - Follow compose logs"
	@echo ""
	@echo "Runtime overrides:"
	@echo "  make compose-dev CONTAINER_RUNTIME=podman"
	@echo "  make compose-dev CONTAINER_RUNTIME=docker"
	@echo "  make compose-dev HOST_GATEWAY=host.containers.internal"
	@echo ""
	@echo "Compatibility aliases:"
	@echo "  make docker-build                 - Alias for container-build"
	@echo "  make docker-run                   - Alias for container-run"
	@echo "  make docker-shell                 - Alias for container-shell"

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

smoke-api:
	uv run python scripts/smoke_backend.py

container-info:
	@echo "CONTAINER_RUNTIME=$(CONTAINER_RUNTIME)"
	@echo "COMPOSE=$(COMPOSE)"
	@echo "HOST_GATEWAY=$(HOST_GATEWAY)"
	@$(CONTAINER_RUNTIME) --version
	@$(COMPOSE) version

container-build:
	$(CONTAINER_RUNTIME) build -t $(APP_NAME) .

container-run: env-check
	$(CONTAINER_RUNTIME) run --rm \
		--env-file $(ENV_FILE) \
		-e APP_HOST=0.0.0.0 \
		-e APP_PORT=$(APP_PORT) \
		-p $(APP_PORT):$(APP_PORT) \
		$(APP_NAME)

container-shell:
	$(CONTAINER_RUNTIME) run --rm -it --entrypoint /bin/bash $(APP_NAME)

compose-dev:
	HOST_GATEWAY=$(HOST_GATEWAY) $(COMPOSE) -f docker-compose.dev.yaml up --build

compose-down:
	$(COMPOSE) -f docker-compose.dev.yaml down

compose-logs:
	$(COMPOSE) -f docker-compose.dev.yaml logs -f
