---
title: "RAG"
type: "concept"
created: "2026-10-03"
summary: "Retrieval-Augmented Generation is the query-time retrieval baseline that the LLM Wiki pattern contrasts against by compiling knowledge into a persistent, compounding wiki."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["architecture", "knowledge-base", "llm", "rag", "retrieval"]
---

# RAG

Retrieval-Augmented Generation (RAG) is the dominant pattern for using LLMs with document collections: files are uploaded, relevant chunks are retrieved at query time, and the model generates an answer from those fragments. The LLM Wiki pattern explicitly positions RAG as the baseline it departs from, because RAG re-derives knowledge on every question rather than accumulating it. Understanding this distinction is central to the source's core argument.

## Definition

RAG is a workflow in which an LLM retrieves relevant chunks from a corpus of documents at query time and uses them to ground a generated answer. The source describes the typical experience as: "you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer." It notes that this "works," but frames it as a starting point rather than an endpoint. [[LLM Wiki Pattern]]

## How it works

In the RAG model, the corpus is indexed for later retrieval, and each query triggers a fresh search over that index. The model then synthesizes an answer from the retrieved fragments. The source highlights a key limitation: "the LLM is rediscovering knowledge from scratch on every question. There's no accumulation." A subtle question that requires synthesizing five documents forces the LLM to "find and piece together the relevant fragments every time. Nothing is built up." [[LLM Wiki Pattern]]

## Contrast with the LLM Wiki pattern

The LLM Wiki pattern inverts the timing of the work. Instead of retrieving from raw documents at query time, the LLM "incrementally builds and maintains a persistent wiki" — a structured, interlinked collection of markdown files that sits between the user and the raw sources. When a new source arrives, the LLM reads it, extracts key information, and integrates it into the existing wiki: updating entity pages, revising topic summaries, and flagging contradictions. The knowledge is "compiled once and then kept current, not re-derived on every query." [[LLM Wiki Pattern]]

The core difference the source draws is that the wiki is "a persistent, compounding artifact": cross-references already exist, contradictions are already flagged, and the synthesis already reflects everything read. RAG, by contrast, produces a one-off answer that disappears into chat history unless manually saved. [[LLM Wiki Pattern]]

## Examples

The source names several systems that operate in the RAG style: "NotebookLM, ChatGPT file uploads, and most RAG systems work this way." These retrieve and answer per query without building a durable, interlinked knowledge base. [[LLM Wiki Pattern]]

## Related

- [[LLM Wiki]] — the persistent, compounding artifact that the LLM maintains in place of query-time retrieval.
- [[LLM Wiki Pattern]] — the overall pattern that contrasts with RAG and explains why the distinction matters.
- [[Ingest]] — the operation that replaces RAG's per-query retrieval by integrating a new source into the wiki.
- [[Memex]] — Vannevar Bush's 1945 vision of a curated, associative knowledge store, which the source links in spirit to the wiki approach rather than to RAG.

## Sources

- [[LLM Wiki Pattern]] (raw file: raw/karpathy-llm-wiki.md)
