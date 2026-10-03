---
title: "Schema"
type: "concept"
created: "2026-10-03"
summary: "The configuration document that defines wiki structure, conventions, and workflows, turning a generic LLM into a disciplined wiki maintainer."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["agents", "configuration", "conventions", "llm-wiki", "workflows"]
---

# Schema

The Schema is the configuration document (e.g. `CLAUDE.md` for Claude Code or `AGENTS.md` for Codex) that tells the LLM how the wiki is structured, what the conventions are, and what workflows to follow when ingesting sources, answering questions, or maintaining the wiki. It is the key file that makes the LLM a disciplined wiki maintainer rather than a generic chatbot [[LLM Wiki Pattern]].

## Definition

The Schema is one of the three architectural layers of the LLM Wiki, alongside the raw sources and the wiki itself. It is a document that codifies the rules of the knowledge base: directory structure, page formats, naming conventions, frontmatter requirements, and the step-by-step procedures for each operation [[LLM Wiki Pattern]].

## How it works

The Schema serves as the standing instruction set that the LLM agent reads at the start of every session. It defines:

- **Structure**: the directory layout (e.g. `raw/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/analyses/`) and the role of each folder.
- **Conventions**: page formats, frontmatter fields, linking syntax (e.g. `[[Exact Title]]`), section headings, and how to handle contradictions.
- **Workflows**: the specific steps for [[Ingest]], [[Lint]], and query operations, including what to update, what to log, and how to cite sources.

The Schema is not static. The human and the LLM co-evolve it over time as they figure out what works for their specific domain. Workflows that are developed and refined during sessions should be documented back into the Schema so that future sessions inherit the improved process [[LLM Wiki Pattern]].

## Relationship to other components

- **Raw sources**: The Schema defines how the LLM should treat the immutable source documents — read-only, never modified.
- **The wiki**: The Schema governs how the LLM creates, updates, and maintains the markdown pages that make up the wiki.
- **Index and log**: The Schema specifies the format and update rules for `index.md` and `log.md`, ensuring consistent navigation and audit trails.

## Why it matters

Without a Schema, the LLM would have to improvise its approach on every interaction, leading to inconsistent structure, missed cross-references, and lost context between sessions. The Schema externalizes the discipline: it encodes the bookkeeping rules that humans typically abandon because the maintenance burden grows faster than the value. By making the conventions explicit and persistent, the Schema ensures that the LLM's maintenance work is systematic, reproducible, and compounding [[LLM Wiki Pattern]].

## Examples

A typical Schema might specify:
- One subject per page; filename equals page title.
- YAML frontmatter with `title`, `type`, `summary`, `sources`, `tags`, `created`, `updated`.
- Body starts with a 1–3 sentence overview, then `## ` sections.
- Every non-obvious fact must trace back to a source page link.
- Contradictions are flagged with a `> [!warning] Contradiction` callout, never silently overwritten.
- After editing, run a reindex command and append a log entry.

## Related

- [[LLM Wiki Pattern]] — the overall pattern the Schema instantiates.
- [[Ingest]] — the primary workflow the Schema governs.
- [[Lint]] — the health-check workflow the Schema defines.
- [[LLM Wiki]] — the broader concept of the persistent, compounding knowledge base.
