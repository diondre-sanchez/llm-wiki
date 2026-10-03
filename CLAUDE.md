@AGENTS.md

## Working on the code

- Python package in `src/llmwiki/`; config in `wiki.toml`; run with `uv run wiki <command>`.
- Providers live in `providers.py`. Every LLM backend implements `complete(system, prompt, schema=None) -> str`.
- Keep the core dependency-free (stdlib only). New integrations go behind optional extras in `pyproject.toml`.
