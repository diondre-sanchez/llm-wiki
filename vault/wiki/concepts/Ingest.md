---
title: "Ingest"
type: "concept"
created: "2026-10-03"
summary: "The core operation of reading a new source, writing its summary, and updating all relevant wiki pages to compound knowledge."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["knowledge-management", "llm-wiki", "operations", "workflow"]
---

# Ingest

## Definition

Ingest is one of the three core operations in the LLM Wiki pattern, alongside Query and Lint. It is the process of processing a new source document by reading it, extracting key information, and integrating that knowledge into the existing wiki structure. Unlike RAG systems that merely index documents for later retrieval, ingest actively compiles knowledge into a persistent, interlinked artifact [[LLM Wiki Pattern]].

## How it works

The ingest workflow follows a specific sequence of actions performed by the LLM agent:

1. **Read the source**: The LLM reads the new document from the immutable raw sources collection.
2. **Discuss takeaways**: The LLM may discuss key points with the human to clarify emphasis and context.
3. **Write a summary page**: A new page is created in `wiki/sources/` containing a structured summary of the document.
4. **Update the index**: The `index.md` catalog is updated to include the new page.
5. **Update entity and concept pages**: The LLM identifies existing pages for entities, concepts, or analyses that are materially touched by the new source and updates them with new facts, cross-references, or contradictions.
6. **Append to the log**: An entry is added to `log.md` recording the operation, timestamp, and subject.

A single ingest operation can touch 10-15 wiki pages, as the new source may relate to multiple entities, concepts, and existing analyses [[LLM Wiki Pattern]]. This breadth of impact is a key advantage over traditional note-taking, where a new source often remains isolated.

## Workflow variations

The source document notes two primary approaches to ingestion:

- **Supervised, one-at-a-time**: The human stays involved, reading summaries, checking updates, and guiding the LLM on what to emphasize. This is preferred for complex or high-stakes sources.
- **Batch ingestion**: Multiple sources are processed at once with less supervision. This is suitable for routine or lower-priority material.

The chosen workflow should be documented in the schema file (e.g., `CLAUDE.md` or `AGENTS.md`) so that future LLM sessions follow the same conventions [[LLM Wiki Pattern]].

## Relationship to other operations

Ingest is the primary mechanism by which the wiki compounds. Each new source adds to the existing synthesis, strengthens or challenges prior claims, and creates new cross-references. This contrasts with Query, which retrieves and synthesizes from the existing wiki, and Lint, which health-checks the wiki for contradictions, orphans, and stale claims [[LLM Wiki Pattern]].

The ingest operation is what makes the wiki a "persistent, compounding artifact" rather than a static collection of summaries. The cross-references are already there, the contradictions have already been flagged, and the synthesis already reflects everything that has been read [[LLM Wiki Pattern]].

## Related

- [[LLM Wiki Pattern]] — the overall pattern that defines the three core operations.
- [[Lint]] — the periodic health-check operation that complements ingest.
- [[Schema]] — the configuration file that defines ingest conventions and workflows.
- [[RAG]] — the alternative approach that retrieves from raw documents at query time without compiling knowledge.

## Sources

- [[LLM Wiki Pattern]] (raw file: `raw/karpathy-llm-wiki.md`)
