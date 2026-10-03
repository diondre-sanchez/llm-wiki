# llm-wiki

A local-first take on [Karpathy's LLM-Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
An LLM compiles your sources into an interlinked markdown wiki once, then answers questions from
those compiled pages using hybrid (keyword + vector) retrieval. It is RAG over a curated wiki
instead of over raw chunks.

- **Engine:** local Ollama by default; switch to Claude by changing one setting.
- **Search:** BM25 + local embeddings (`nomic-embed-text`), fused with reciprocal rank fusion. Always local.
- **Storage:** plain markdown with YAML frontmatter and `[[wikilinks]]`. Open `vault/` in Obsidian.
- **Core dependencies:** none (Python stdlib). PDF and Claude support are optional extras.

## Setup

```bash
uv sync --extra pdf
```

```bash
uv run wiki status
```

`status` pings the LLM and the embedding model so you know both are reachable.

## Use

```bash
uv run wiki ingest path/to/article.md
```

```bash
uv run wiki query "What are the tradeoffs between X and Y?"
```

```bash
uv run wiki query "Compare X and Y" --save
```

```bash
uv run wiki lint
```

| Command | What it does |
|---|---|
| `ingest <files or folders>` | Copies the source into `vault/raw/`, writes a source summary page, and creates or updates entity and concept pages. Supports md, txt, pdf and html. |
| `query "<question>" [--save] [-k N]` | Retrieves the top pages and answers with `[[citations]]`. `--save` files the answer back as an analysis page. |
| `search "<text>"` | Hybrid search only, no LLM call. |
| `lint [--no-llm]` | Broken links, orphans, missing summaries, uncited pages; with the LLM also duplicates, contradictions and suggested pages. Writes `wiki/lint-report.md`. |
| `reindex` | Rebuilds `index.md` and refreshes embeddings after you edit pages by hand. |
| `init` | Creates the vault folders. |

## Switching to Claude

```bash
uv sync --extra pdf --extra claude
```

Then set `ANTHROPIC_API_KEY` (or run `ant auth login`) and either change `provider = "anthropic"`
in `wiki.toml` or override a single run:

```bash
uv run wiki --provider anthropic ingest vault/raw/hard-paper.pdf
```

A good hybrid workflow: ingest your important or difficult sources with Claude for higher-quality
pages, and run queries and lint with the local model. Embeddings stay local either way.

You can also point Claude Code (or Codex) at this folder and let it edit the vault directly.
`AGENTS.md` is the shared schema, and `CLAUDE.md` imports it.

## Layout

```
AGENTS.md          schema: conventions the LLM follows (also the system prompt)
wiki.toml          provider, models, limits
src/llmwiki/       providers.py, vault.py, search.py, ops.py, cli.py
vault/raw/         immutable sources
vault/wiki/        sources/ entities/ concepts/ analyses/ index.md log.md
.cache/            embedding cache (safe to delete)
```

## Tuning for local models

- `qwen3.8:27b` with `num_ctx = 16384` fits on a 24 GB GPU. `phi4:14b` is faster but writes weaker pages.
- Sources longer than `max_source_chars` are condensed chunk by chunk before planning, so prompts fit the context window.
- `think = true` lets thinking models reason before answering. It is slower, and sometimes better at merging contradictions.
