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
