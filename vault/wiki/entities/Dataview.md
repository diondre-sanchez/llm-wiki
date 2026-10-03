---
title: "Dataview"
type: "entity"
created: "2026-10-03"
summary: "An Obsidian plugin that runs queries over page frontmatter to generate dynamic tables and lists from LLM-added metadata."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["dataview", "frontmatter", "obsidian", "plugin", "querying"]
---

# Dataview

Dataview is an Obsidian plugin that executes queries over page frontmatter, enabling the generation of dynamic tables and lists from metadata such as tags and dates.

## Overview

Dataview extends Obsidian's capabilities by allowing users to query the YAML frontmatter of markdown files. In the context of an LLM-maintained wiki, this is particularly useful because the LLM can add structured metadata (tags, dates, source counts) to pages during the ingest process, and Dataview can then render that metadata into dynamic views without manual formatting.

## How it works

- **Frontmatter queries**: Dataview reads the YAML frontmatter of each note and allows users to write queries that filter, sort, and display fields.
- **Dynamic views**: Instead of static lists, Dataview generates tables and lists that update automatically as frontmatter changes.
- **LLM integration**: When an LLM agent adds metadata to wiki pages (e.g., `tags`, `created`, `updated`), Dataview can surface this data in a structured, readable format.

## Use cases

- Generating a catalog of all wiki pages with their summaries and tags.
- Creating a timeline of ingested sources based on date fields.
- Building dynamic lists of entities or concepts filtered by specific metadata.

## Related

- [[Obsidian]]: The markdown editor and knowledge base platform where Dataview operates.
- [[LLM Wiki Pattern]]: The broader pattern in which LLMs maintain wiki pages with structured frontmatter that Dataview can query.
- [[Schema]]: The configuration document that defines frontmatter conventions, which Dataview relies on for consistent querying.

## Sources

- [[LLM Wiki Pattern]] (raw file: raw/karpathy-llm-wiki.md)
