---
title: "qmd"
type: "entity"
created: "2026-10-03"
summary: "A local markdown search engine with hybrid BM25/vector search and LLM re-ranking, used to scale wiki search beyond the index file."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["cli", "markdown", "mcp", "search", "tooling"]
---

# qmd

## Overview

qmd is a local search engine designed for markdown files, featuring hybrid BM25/vector search and LLM re-ranking, all running on-device. It is mentioned as an optional tool for scaling wiki search beyond the simple index file approach when the wiki grows in size [[LLM Wiki Pattern]].

## Key facts

- **Hybrid search**: Combines BM25 (keyword-based) and vector (semantic) search methods [[LLM Wiki Pattern]].
- **LLM re-ranking**: Uses a local LLM to re-rank search results for improved relevance [[LLM Wiki Pattern]].
- **On-device**: All processing happens locally, no cloud dependency [[LLM Wiki Pattern]].
- **Dual interface**: Provides both a CLI (for shell-out usage by LLM agents) and an MCP server (for native tool integration) [[LLM Wiki Pattern]].
- **Purpose**: Serves as a proper search layer when the wiki outgrows the simple `index.md` catalog approach, which works well at moderate scale (~100 sources, hundreds of pages) [[LLM Wiki Pattern]].

## Relationships

- **[[LLM Wiki Pattern]]**: qmd is recommended as an optional CLI tool for the LLM Wiki pattern, specifically for the "search engine over the wiki pages" use case when the index file is no longer sufficient [[LLM Wiki Pattern]].
- **[[Ingest]]**: While not directly part of the ingest workflow, qmd supports the query operation by enabling efficient page discovery in larger wikis [[LLM Wiki Pattern]].
- **[[RAG]]**: qmd provides a local, markdown-specific alternative to embedding-based RAG infrastructure, which the LLM Wiki pattern explicitly avoids at moderate scale [[LLM Wiki Pattern]].

## Sources

- [[LLM Wiki Pattern]] (raw file: raw/karpathy-llm-wiki.md) — Mentions qmd in the "Optional: CLI tools" section as a good option for local markdown search with hybrid BM25/vector search and LLM re-ranking, available via CLI and MCP server.
