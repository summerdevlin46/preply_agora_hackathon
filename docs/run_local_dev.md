# Run AfterClass locally

This project has three moving parts:

1. FastAPI backend on port `8000`
2. Next.js frontend on port `3000`
3. Optional local OpenAI-compatible model server on port `8081`

The backend and frontend can run in containers. The local model server should usually run on the host machine, especially on Apple Silicon with MLX.

## Option A: Run backend + frontend with Podman

Start the Podman machine:

```bash
podman machine start
```
Start the app stack:

```bash
make compose-dev CONTAINER_RUNTIME=podman HOST_GATEWAY=host.containers.internal
```

Open:

```bash
http://localhost:3000
```

Check backend health:

```bash
curl http://127.0.0.1:8000/api/health
```

Stop the stack:

```bash
make compose-down CONTAINER_RUNTIME=podman
```

Stop the Podman machine when finished:

podman machine stop
## Option B: Run backend + frontend with Docker

Start the app stack:

```bash
make compose-dev CONTAINER_RUNTIME=docker HOST_GATEWAY=host.docker.internal
```

Open:

```bash
http://localhost:3000
```

Stop the stack:

```bash
make compose-down CONTAINER_RUNTIME=docker
```
## Optional: Run local MLX model server on host

Install/sync Apple local dependencies first:

```bash
make sync-apple-local
```

Start the local model server:

```bash
make run-model
```

Check it:

```bash
curl http://127.0.0.1:8081/v1/models
```

When the backend runs in a container, it should reach the host model through:

```bash
http://host.containers.internal:8081/v1
```

for Podman, or:

```bash
http://host.docker.internal:8081/v1
```

for Docker.

## Smoke tests

With backend running:

```bash
make smoke-api
```

Frontend lint:

```bash
podman compose -f docker-compose.dev.yaml exec -T frontend npm run lint
```

or with Docker:

```bash
docker compose -f docker-compose.dev.yaml exec -T frontend npm run lint
```
Expected demo behavior

The local tiny model may fail to return valid JSON. In that case, the backend serves demo fallback content and the frontend shows a fallback warning. This is expected for local smoke testing.

A successful demo path is:

1. Open http://localhost:3000
2. Click Generate Avatar Conversation
3. Confirm the avatar session modal opens
4. Click Launch Session
5. Confirm `/chat/<chat_id>` opens
6. Review the task intro page
