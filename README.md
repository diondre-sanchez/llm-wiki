# llm-wiki

A local-first take on [Karpathy's LLM-Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
An LLM compiles your sources into an interlinked markdown wiki once, then answers questions from
those compiled pages using hybrid (keyword + vector) retrieval. It is RAG over a curated wiki
instead of over raw chunks.

- **Engine:** local Ollama by default; switch to Claude by changing one setting.
- **Search:** BM25 + local embeddings (`nomic-embed-text`), fused with reciprocal rank fusion. Always local.
- **Storage:** plain markdown with YAML frontmatter and `[[wikilinks]]`. Open `vault/` in Obsidian.
- **Core dependencies:** none (Python stdlib). Document conversion, PDF and Claude support are optional extras.

## Setup

```bash
uv sync --extra convert
```

`convert` installs [MarkItDown](https://github.com/microsoft/markitdown) for Word, PowerPoint, Excel,
EPUB and Outlook files, and better PDF and HTML extraction. For a minimal install, `--extra pdf` alone
handles markdown, text, PDF and HTML.

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
| `ingest <files or folders>` | Copies the source into `vault/raw/`, writes a source summary page, and creates or updates entity and concept pages. See [Source formats](#source-formats). |
| `query "<question>" [--save] [-k N]` | Retrieves the top pages and answers with `[[citations]]`. `--save` files the answer back as an analysis page. |
| `search "<text>"` | Hybrid search only, no LLM call. |
| `lint [--no-llm]` | Broken links, orphans, missing summaries, uncited pages; with the LLM also duplicates, contradictions and suggested pages. Writes `wiki/lint-report.md`. |
| `reindex` | Rebuilds `index.md` and refreshes embeddings after you edit pages by hand. |
| `mcp [--host H] [--port P]` | Serves the wiki to MCP clients such as Open WebUI, Claude Desktop and Cursor. Needs `--extra mcp`. See [docs/open-webui.md](docs/open-webui.md). |
| `init` | Creates the vault folders. |

## Source formats

Drop files into `vault/raw/` (or anywhere) as they are; no conversion needed. Text is extracted in
memory at ingest time, and files in `raw/` are never modified.

| Format | Needs | Notes |
|---|---|---|
| `.md` `.markdown` `.txt` `.rst` | nothing | Best results |
| `.pdf` | `pdf` or `convert` | Needs a text layer: scanned PDFs must be OCR'd first |
| `.html` `.htm` | nothing (`convert` is cleaner) | Obsidian Web Clipper gives the cleanest web articles |
| `.docx` `.pptx` `.xlsx` `.xls` `.epub` `.msg` `.csv` `.json` `.xml` `.ipynb` | `convert` | Converted to markdown with MarkItDown, tables included |

Folder ingest skips unsupported files and lists them. A file that can't be read (wrong type, corrupt,
no text) is reported and left out of `raw/`; the rest of the batch continues and the command exits 1.

## Open WebUI and other MCP clients

`uv run wiki mcp` starts a read-only MCP server on `http://127.0.0.1:8765/mcp` with `wiki_search`,
`wiki_read` and `wiki_index` tools. Register it in Open WebUI as an external tool server and the
model you chat with can search and cite your wiki. Setup steps, security notes and a Windows
start-at-logon script: [docs/open-webui.md](docs/open-webui.md).

## Switching to Claude

```bash
uv sync --extra convert --extra claude
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
src/llmwiki/       providers.py, sources.py, vault.py, search.py, ops.py, mcp_server.py, cli.py
scripts/           start-mcp.ps1, install-startup-task.ps1
docs/              open-webui.md
vault/raw/         immutable sources
vault/wiki/        sources/ entities/ concepts/ analyses/ index.md log.md
.cache/            embedding cache (safe to delete)
```

## Tuning for local models

- `qwen3.8:27b` with `num_ctx = 16384` fits on a 24 GB GPU. `phi4:14b` is faster but writes weaker pages.
- Sources longer than `max_source_chars` are condensed chunk by chunk before planning, so prompts fit the context window.
- `think = true` lets thinking models reason before answering. It is slower, and sometimes better at merging contradictions.
