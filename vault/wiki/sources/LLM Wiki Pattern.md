---
title: "LLM Wiki Pattern"
type: "source"
created: "2026-10-03"
summary: "A pattern for building personal knowledge bases where an LLM incrementally maintains a persistent, interlinked markdown wiki instead of re-deriving answers via RAG."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["knowledge-management", "llm", "obsidian", "rag", "wiki"]
---

# LLM Wiki Pattern

## What it is

An idea file by Andrej Karpathy describing a pattern for building personal knowledge bases with LLMs. It is designed to be copy-pasted to an LLM agent (Codex, Claude Code, etc.) to communicate the high-level idea, with the agent building out the specifics in collaboration with the user. The document is intentionally abstract and modular — it describes the pattern, not a specific implementation. [[LLM Wiki Pattern]]

## Key claims

- **Core difference from RAG**: Instead of retrieving chunks at query time and re-deriving knowledge every question, the LLM incrementally builds and maintains a persistent wiki of interlinked markdown files. Knowledge is compiled once and kept current, not re-derived. The wiki is a "persistent, compounding artifact" where cross-references, contradictions, and synthesis already exist. [[RAG]]
- **Division of labor**: The human curates sources, directs analysis, and asks questions. The LLM does all summarizing, cross-referencing, filing, and bookkeeping. "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." [[Obsidian]]
- **Three-layer architecture**: (1) Raw sources (immutable, source of truth), (2) The wiki (LLM-generated markdown, LLM-owned), (3) The schema (a config document like CLAUDE.md or AGENTS.md that defines conventions and workflows). [[Schema]]
- **Three operations**: Ingest (process a new source, touching 10-15 pages), Query (answer from the wiki, file good answers back as new pages), and Lint (health-check for contradictions, stale claims, orphans, missing pages). [[Ingest]] [[Lint]]
- **Indexing and logging**: `index.md` is a content-oriented catalog updated on every ingest; `log.md` is an append-only chronological record. At moderate scale (~100 sources, hundreds of pages), the index file avoids the need for embedding-based RAG infrastructure.
- **Why it works**: The maintenance burden (cross-references, consistency, contradiction tracking) is what causes humans to abandon wikis. LLMs don't get bored and can touch 15 files in one pass, making the cost of maintenance near zero.
- **Historical connection**: Related in spirit to Vannevar Bush's Memex (1945) — a personal, curated knowledge store with associative trails. Bush's vision was private, actively curated, with connections as valuable as documents. The LLM solves the maintenance problem Bush couldn't. [[Vannevar Bush]] [[Memex]]

## Data and quotes

- "The wiki is a persistent, compounding artifact. The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read."
- "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."
- "A single source might touch 10-15 wiki pages."
- "This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure."
- "The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. The LLM's job is everything else."
- "The part he couldn't solve was who does the maintenance. The LLM handles that."
- Example use cases: personal tracking, research, reading a book (comparing to fan wikis like Tolkien Gateway), business/team wikis, competitive analysis, due diligence, trip planning, course notes. [[Tolkien Gateway]]
- Tooling mentions: qmd (local markdown search with BM25/vector + LLM re-ranking), Marp (slide decks), Dataview (frontmatter queries), Obsidian Web Clipper, git for version control. [[qmd]] [[Marp]] [[Dataview]]

## Pages touched

- [[LLM Wiki Pattern]] — the core pattern described by this source
- [[RAG]] — the approach this pattern contrasts with
- [[Obsidian]] — the recommended IDE/viewer for the wiki
- [[Schema]] — the configuration layer defining conventions
- [[Ingest]] — the operation of processing a new source
- [[Lint]] — the health-check operation
- [[Vannevar Bush]] — historical inspiration (Memex)
- [[Memex]] — the 1945 concept this pattern echoes
- [[Tolkien Gateway]] — cited as an example of a rich interlinked wiki
- [[qmd]] — optional search tooling
- [[Marp]] — optional slide deck output
- [[Dataview]] — optional frontmatter query plugin
