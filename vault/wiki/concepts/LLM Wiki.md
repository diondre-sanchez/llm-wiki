---
title: "LLM Wiki"
type: "concept"
created: "2026-10-03"
summary: "A persistent, LLM-maintained knowledge base that compounds over time instead of re-deriving answers via RAG."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["compounding", "knowledge-management", "llm", "rag-alternative", "wiki"]
---

# LLM Wiki

## Definition

The LLM Wiki is a pattern for building personal knowledge bases where an LLM incrementally builds and maintains a persistent, interlinked collection of markdown files. Unlike RAG systems that retrieve and re-derive knowledge from raw documents on every query, the LLM Wiki compiles knowledge once and keeps it current, allowing the knowledge base to compound over time [[LLM Wiki Pattern]].

## How it works

The core mechanism replaces query-time retrieval with continuous integration. When a new source is added, the LLM reads it, extracts key information, and integrates it into the existing wiki by updating entity pages, revising topic summaries, and flagging contradictions. The result is a persistent artifact where cross-references, syntheses, and conflict notes already exist, rather than being reconstructed from scratch for each question [[LLM Wiki Pattern]].

The architecture consists of three layers: immutable raw sources, the LLM-maintained wiki directory, and a schema document that defines conventions and workflows. The LLM owns the wiki layer entirely, handling summarizing, cross-referencing, filing, and bookkeeping, while the human focuses on sourcing, exploration, and asking questions [[LLM Wiki Pattern]].

Key operations include:
- **Ingest**: Processing new sources by writing summary pages and updating related entity and concept pages across the wiki.
- **Query**: Synthesizing answers from existing wiki pages with citations, with the option to file valuable answers back into the wiki as new pages.
- **Lint**: Periodically health-checking the wiki for contradictions, stale claims, orphan pages, and missing cross-references [[LLM Wiki Pattern]].

## Examples

The pattern applies to various contexts where knowledge accumulates over time:
- **Personal**: Tracking goals, health, and psychology by filing journal entries and articles into a structured self-portrait.
- **Research**: Building a comprehensive wiki with an evolving thesis over weeks or months of reading papers and reports.
- **Reading**: Creating a companion wiki for a book, similar to fan wikis like [[Tolkien Gateway]], with pages for characters, themes, and plot threads.
- **Business**: Maintaining an internal wiki fed by Slack threads, meeting transcripts, and project documents, with the LLM handling the maintenance burden that teams typically avoid [[LLM Wiki Pattern]].

## Related

The idea is related in spirit to Vannevar Bush's [[Memex]] (1945), a vision of a personal, curated knowledge store with associative trails between documents. Bush's concept was private and actively curated, with connections between documents as valuable as the documents themselves. The key difference is that Bush could not solve the maintenance problem, whereas the LLM handles the tedious bookkeeping that causes humans to abandon wikis [[LLM Wiki Pattern]].

This pattern contrasts with standard [[RAG]] approaches, which work but lack accumulation. In RAG, the LLM rediscovering knowledge from scratch on every question means nothing is built up, whereas the LLM Wiki ensures the synthesis reflects everything previously read [[LLM Wiki Pattern]].

## Sources

- [[LLM Wiki Pattern]]
