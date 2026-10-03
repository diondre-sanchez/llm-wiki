---
title: "How does the LLM Wiki differ from RAG, and when would I add search"
type: "analysis"
created: "2026-10-03"
summary: "Answer to: How does the LLM Wiki differ from RAG, and when would I add search?"
updated: "2026-10-03"
tags: ["analysis"]
---

# How does the LLM Wiki differ from RAG, and when would I add search

## How the LLM Wiki differs from RAG

The core difference is **when the work happens** and **whether knowledge accumulates**.

- **RAG** retrieves relevant chunks from raw documents *at query time* and generates an answer from those fragments. The LLM is "rediscovering knowledge from scratch on every question. There's no accumulation." A subtle question that requires synthesizing five documents forces the model to "find and piece together the relevant fragments every time. Nothing is built up." [[RAG]]
- **LLM Wiki** inverts this: the LLM "incrementally builds and maintains a persistent wiki" of interlinked markdown files. When a new source arrives, the LLM reads it, extracts key information, and integrates it into existing pages—updating entities, revising summaries, and flagging contradictions. The result is a "persistent, compounding artifact" where cross-references, syntheses, and conflict notes already exist. Knowledge is "compiled once and then kept current, not re-derived on every query." [[LLM Wiki Pattern]] [[LLM Wiki]]

In short: RAG produces a one-off answer that disappears into chat history; the LLM Wiki produces a durable, structured knowledge base that improves with every new source. [[RAG]]

## When to add search

The wiki's default navigation is a simple `index.md` catalog, which "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure." [[LLM Wiki Pattern]]

You would add a dedicated search tool like **qmd** when the wiki outgrows that moderate scale and the index file is no longer sufficient for efficient page discovery. qmd provides hybrid BM25/vector search with LLM re-ranking, all running locally, and is available via CLI or MCP server. It serves as "a proper search layer" for larger wikis without reintroducing the cloud-dependent RAG infrastructure the pattern avoids. [[qmd]] [[LLM Wiki Pattern]]
