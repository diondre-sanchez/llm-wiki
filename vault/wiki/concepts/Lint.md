---
title: "Lint"
type: "concept"
created: "2026-10-03"
summary: "A periodic wiki health-check operation that identifies contradictions, stale claims, orphan pages, and missing cross-references to maintain knowledge base integrity."
updated: "2026-10-03"
sources: ["karpathy-llm-wiki.md"]
tags: ["data-integrity", "knowledge-management", "llm-operations", "quality-assurance", "wiki-maintenance"]
---

# Lint

## Definition

Lint is one of the three core operations in the LLM Wiki pattern, functioning as a periodic health-check mechanism for the wiki. It involves asking the LLM to systematically review the wiki for structural and content issues that accumulate over time, ensuring the knowledge base remains coherent and useful as it grows [[LLM Wiki Pattern]].

## How it works

The Lint operation targets several specific categories of wiki degradation:

- **Contradictions between pages**: Identifying where different wiki pages make conflicting claims about the same facts or concepts
- **Stale claims**: Detecting assertions that have been superseded by newer sources or more recent information
- **Orphan pages**: Finding pages with no inbound links from other wiki pages, indicating they are disconnected from the knowledge graph
- **Missing pages**: Identifying important concepts that are mentioned throughout the wiki but lack their own dedicated page
- **Missing cross-references**: Discovering opportunities to link related pages that should be connected but currently aren't
- **Data gaps**: Recognizing areas where the wiki could be enriched with additional information, potentially through web searches or new sources

The LLM is particularly effective at suggesting new questions to investigate and identifying new sources that would fill identified gaps [[LLM Wiki Pattern]]. This proactive discovery capability helps the wiki evolve beyond just recording existing knowledge to actively guiding further research.

## Relationship to other operations

Lint complements the other two core operations: [[Ingest]] and Query. While Ingest adds new knowledge to the wiki and Query extracts answers from it, Lint maintains the structural integrity and coherence of the entire knowledge base. Together, these three operations create a complete lifecycle for knowledge management: adding, using, and maintaining.

The Lint operation is especially important because the maintenance burden is what typically causes human-maintained wikis to fail. As noted in the LLM Wiki pattern, humans abandon wikis because the maintenance burden grows faster than the value, but LLMs don't get bored and can touch many files in one pass, making the cost of maintenance near zero [[LLM Wiki Pattern]].

## Examples

A typical Lint pass might reveal:
- Two entity pages describing the same person with different birth dates
- A concept page that references a term mentioned in five other pages but has no dedicated page
- A source summary that contradicts a claim in an entity page, with the contradiction not yet flagged
- A cluster of related pages that should be cross-linked but currently have no connections
- An outdated claim about a product's features that has been superseded by a newer source

## Related

- [[Ingest]]: The operation that adds new sources to the wiki
- [[Query]]: The operation that extracts answers from the wiki
- [[LLM Wiki]]: The overall pattern that Lint is part of
- [[Schema]]: The configuration document that defines wiki conventions and workflows
- [[Obsidian]]: The IDE used to browse and visualize the wiki, including graph view for identifying orphans

## Sources

- [[LLM Wiki Pattern]] (raw file: raw/karpathy-llm-wiki.md)
