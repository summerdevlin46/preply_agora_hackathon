# 🪞 Mirror — Post-Lesson Language Coach

Agentic pipeline that:
- parses worksheets (OCR)
- extracts style + structure
- generates new exercises for a different topic

---

# 🚀 Project Structure

- `main` → stable only  
- `dev` → active work  
- `draft` → experiments  

---

# ⚙️ Setup

## Requirements

- Python 3.13+
- `uv` (https://github.com/astral-sh/uv)

Optional system dependencies (OCR):

```bash
./scripts/system_deps.sh install
```

# Install dependencies

```bash
make setup
```

for apple + local models

```bash
make setup-apple
```

# Running the app

```bash
make run
```

Dev mode:
```bash
make run-dev
```

Public share:
```bash
make run-share
```

# Model backends

App supports 3 backends:

## Local OSS (rec for dev)

```bash
uv run python -m mlx_lm server \
  --model HuggingFaceTB/SmolLM2-360M-Instruct \
  --host 127.0.0.1 \
  --port 8081
```

### Run app

```bash
make run
```

`.env`

```bash
MIRROR_MODEL_BACKEND=local_oss
LOCAL_OSS_BASE_URL=http://127.0.0.1:8081/v1
LOCAL_OSS_MODEL=HuggingFaceTB/SmolLM2-360M-Instruct
```

## OpenAI

```bash
MIRROR_MODEL_BACKEND=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5
```

## Hugging Face (inference providers)

```bash
MIRROR_MODEL_BACKEND=huggingface
HF_TOKEN=...
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct:novita
```

- Requires provider-supported models
- may consume credits

## Testing

```bash
make test
```

## Useful commands

```bash
make clean
make update
make deps-check
```

## Secrets and Deployment

### Local

Use .env (never commit)

### Github

Add to **GitHub Secrets**
- `OPEN_API_KEY`
- `HF_TOKEN`

### AWS (future)
- Use AWS Secrets Manager
- Inject into runtime environment

# Architcture notes:

Pipeline (LangGraph):

`worksheet → excerpt → style → prompt → generate → verify → repair`

Features:

- retry/repair loop
- prompt shaping
- backend abstraction (OpenAI / HF / local)

# TODO

- [ ] CI/CD
- [ ] better prompt tuning
- [ ] streaming responses in Gradio
- [ ] caching worksheet embeddings
- [ ] better exercise formatting (important for demo quality)
- [ ] caching OCR + embeddings
- [ ] improve verification node
