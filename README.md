# Hackathon project

3 main branches
- main, only to merge
- dev, work on this
- draft

# How to
TODO: Update instructions with the make command equivalents!!!!

Entry point: Gradio UI + Typer CLI
Run:  uv run python app.py

- To create a public link, set `share=True` in `launch()

Test: uv pytest tests/test_app.py -v

NEW VER:
```bash
make setup
make run-dev
```

# Requirements

uv

Always cheeck if dependencies available with ` ./scripts/system_deps.sh check`

# Important missing todos.

update .venv to `MIRROR_MODEL_BACKEND=huggingface`

add ci/cd
move secrets from local to one branch in dev for CI/CD. USE AWS Secrets Manager

Put OPENAI_API_KEY and HF_TOKEN in GitHub Secrets

When you deploy to AWS, store those same real values in AWS Secrets Manager

Keep OPENAI_MODEL, HF_MODEL, and MIRROR_MODEL_BACKEND as environment config unless you have a reason to hide them
