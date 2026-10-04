"""The three LLM-Wiki operations: ingest, query, lint."""

import json
import re
import shutil
from pathlib import Path

from .config import Config
from .providers import LLM
from .search import SearchIndex
from .vault import Page, Vault, clean_title

def plan_schema(existing_titles: list[str]) -> dict:
    """Updates may only name existing pages (enforced by an enum), so the model can't misspell them."""
    update_title = {"type": "string", "enum": existing_titles} if existing_titles else {"type": "string"}
    return {
        "type": "object",
        "properties": {
            "source_title": {"type": "string"},
            "updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"title": update_title, "why": {"type": "string"}},
                    "required": ["title", "why"],
                    "additionalProperties": False,
                },
            },
            "new_pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "type": {"type": "string", "enum": ["entity", "concept"]},
                        "why": {"type": "string"},
                    },
                    "required": ["title", "type", "why"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["source_title", "updates", "new_pages"],
        "additionalProperties": False,
    }


PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "body": {"type": "string"},
    },
    "required": ["summary", "tags", "body"],
    "additionalProperties": False,
}

CONTRADICTION_SCHEMA = {
    "type": "object",
    "properties": {
        "duplicate": {"type": "boolean"},
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_a": {"type": "string"},
                    "claim_b": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["claim_a", "claim_b", "note"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["duplicate", "contradictions"],
    "additionalProperties": False,
}

GAPS_SCHEMA = {
    "type": "object",
    "properties": {
        "missing_pages": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "open_questions": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
    },
    "required": ["missing_pages", "open_questions"],
    "additionalProperties": False,
}


def _json(text: str) -> dict:
    """Parse model JSON, tolerating stray code fences some local models add."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def read_source(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise SystemExit("PDF ingest needs: uv sync --extra pdf") from e
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".html", ".htm"}:
        text = re.sub(r"(?is)<(script|style).*?</\1>", "", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
    return text


class Wiki:
    def __init__(self, cfg: Config, llm: LLM, echo=print):
        self.cfg = cfg
        self.llm = llm
        self.vault = Vault(cfg)
        self.vault.ensure()
        self.index = SearchIndex(cfg, self.vault)
        self.echo = echo
        self.system = cfg.schema_text

    # ------------------------------------------------------------------ ingest

    def ingest(self, src: Path) -> list[str]:
        src = src.resolve()
        raw = self.vault.raw.resolve()
        if raw not in src.parents:
            dest = raw / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
                self.echo(f"  copied into raw/: {dest.name}")
            src = dest
        source_id = src.relative_to(raw).as_posix()

        text = read_source(src).strip()
        if not text:
            raise SystemExit(f"No text could be read from {src}")
        material = self._condense(text)

        self.index.refresh()
        related = self.index.search(material[:3000], k=self.cfg.get("ingest", "related_pages", 8))
        related_txt = "\n".join(f"- [[{p.title}]] ({p.type}): {p.summary}" for p, _ in related) or "(wiki is empty)"

        self.echo("  planning pages...")
        max_pages = self.cfg.get("ingest", "max_pages_per_ingest", 12)
        # Analyses are snapshots of past answers, and sources belong to one raw file; neither is merged into.
        related_titles = [p.title for p, _ in related if p.type in {"entity", "concept"}]
        plan = _json(self.llm.complete(self.system, f"""TASK: plan an ingest.

Read the SOURCE and decide which wiki pages it should change. Knowledge must compound, so:
- updates: EXISTING PAGES that this source adds new facts, examples, or counterpoints to.
  Include every existing page the source says something substantive about.
- new_pages: important entities (people, orgs, products, places, works) and concepts (ideas, methods, terms)
  that have no page yet. Only subjects a reader would look up on their own; skip tools, files,
  and names mentioned only in passing. Never duplicate an existing page under a new name.
- At most {max_pages} pages in total across both lists.
- source_title: a short descriptive title for the source itself.

EXISTING PAGES:
{related_txt}

SOURCE ({source_id}):
{material}""", plan_schema(related_titles)))

        updates = list({u["title"].lower(): u for u in plan["updates"]
                        if u["title"] in related_titles}.values())
        new_pages = []
        for item in plan["new_pages"]:
            item["title"] = clean_title(item["title"])
            if item["title"] and not self.vault.find(item["title"]):
                new_pages.append(item)
        planned = [{"title": u["title"], "type": self.vault.find(u["title"]).type, "why": u["why"]} for u in updates]
        planned = (planned + new_pages)[:max_pages]

        source_title = clean_title(plan["source_title"]) or clean_title(src.stem)
        # A source often shares its name with its main subject; keep the two pages distinct.
        clash = self.vault.find(source_title)
        if any(x["title"].lower() == source_title.lower() for x in planned) or (clash and clash.type != "source"):
            source_title = f"{source_title} (source)"
        known = sorted({p.title for p in self.vault.pages()} | {x["title"] for x in planned} | {source_title})
        touched = []

        self.echo(f"  writing source page: {source_title}")
        self._write(source_title, "source", material, source_id, source_title, known,
                    "Write the SOURCE SUMMARY page: what the source is, its key claims and data, "
                    "notable quotes, and links to the entity/concept pages it touches.")
        touched.append(source_title)

        for item in planned:
            existing = self.vault.find(item["title"])
            verb = "updating" if existing else "creating"
            self.echo(f"  {verb} {item['type']}: {item['title']}")
            self._write(item["title"], item["type"], material, source_id, source_title, known,
                        f"Write the {item['type'].upper()} page for '{item['title']}'. Focus: {item['why']}",
                        existing)
            touched.append(item["title"])

        self.vault.rebuild_index()
        self.vault.log("ingest", source_title,
                       f"source: raw/{source_id} | engine: {self.llm.name}\n"
                       + "\n".join(f"- [[{t}]]" for t in touched))
        self.index.refresh()
        return touched

    def _condense(self, text: str) -> str:
        """Fit long sources into the context window by condensing chunk by chunk."""
        limit = self.cfg.get("ingest", "max_source_chars", 24000)
        if len(text) <= limit:
            return text
        size = self.cfg.get("ingest", "chunk_chars", 12000)
        chunks = [text[i : i + size] for i in range(0, len(text), size)]
        notes = []
        for n, chunk in enumerate(chunks, 1):
            self.echo(f"  condensing chunk {n}/{len(chunks)}...")
            notes.append(self.llm.complete(self.system, f"""TASK: condense part {n} of {len(chunks)} of a long source into dense notes.
Keep every named entity, number, date, definition, claim and notable short quote. Drop filler. Output markdown bullets only.

TEXT:
{chunk}"""))
        return "\n\n".join(notes)

    def _write(self, title: str, page_type: str, material: str, source_id: str, source_title: str,
               known: list[str], instruction: str, existing: Page | None = None) -> Page:
        existing = existing or self.vault.find(title)
        existing_txt = existing.body if existing else "(new page)"
        result = _json(self.llm.complete(self.system, f"""TASK: write one wiki page.

{instruction}

RULES:
- body: the full page in markdown, WITHOUT frontmatter and WITHOUT a top-level '# ' heading. Use '## ' sections.
- If an EXISTING PAGE is given, merge: keep its still-valid content, add the new information, and mark
  disagreements with a '> [!warning] Contradiction' callout citing both sources instead of silently overwriting.
- Link to other pages with [[Exact Title]] - only titles from KNOWN PAGES.
- Attribute new facts to the source by linking its summary page [[{source_title}]] (raw file: raw/{source_id}).
- summary: one sentence (max 25 words) describing the page, for the index.
- tags: 1-5 lowercase topic tags.

KNOWN PAGES: {', '.join(known)}

EXISTING PAGE:
{existing_txt}

SOURCE ({source_id}):
{material}""", PAGE_SCHEMA))
        return self.vault.save(title, page_type, result["body"], result["summary"].strip(),
                               sources=[source_id], tags=result.get("tags", []))

    # ------------------------------------------------------------------- query

    def query(self, question: str, k: int | None = None, save: bool = False) -> str:
        self.index.refresh()
        k = k or self.cfg.get("query", "top_k", 6)
        hits = self.index.search(question, k=k)
        if not hits:
            return "The wiki is empty - ingest some sources first."
        context = "\n\n---\n\n".join(p.text()[:6000] for p, _ in hits)
        answer = self.llm.complete(self.system, f"""TASK: answer a question from the wiki.

Use ONLY the WIKI PAGES below. Cite pages inline as [[Exact Title]].
If the pages do not contain the answer, say what is missing and which sources would fill the gap.
Answer in markdown.

WIKI INDEX (for orientation):
{self.vault.index_text()[:4000]}

WIKI PAGES:
{context}

QUESTION: {question}""")
        if save:
            title = re.sub(r"[?!.]+$", "", question.strip())[:90]
            self.vault.save(title, "analysis", answer, f"Answer to: {question.strip()}"[:200], tags=["analysis"])
            self.vault.rebuild_index()
            self.index.refresh()
            self.echo(f"  saved as [[{title}]]")
        self.vault.log("query", question.strip()[:80],
                       "pages: " + ", ".join(f"[[{p.title}]]" for p, _ in hits) + (" | saved" if save else ""))
        return answer

    # -------------------------------------------------------------------- lint

    def lint(self, use_llm: bool = True) -> str:
        pages = self.vault.pages()
        titles = {p.title.lower() for p in pages} | {p.path.stem.lower() for p in pages}
        inbound = {p.title.lower(): 0 for p in pages}
        broken, no_summary, no_source = [], [], []
        for p in pages:
            for link in p.links:
                if link.lower() not in titles:
                    broken.append((p.title, link))
                elif link.lower() in inbound:
                    inbound[link.lower()] += 1
            if not p.summary:
                no_summary.append(p.title)
            if p.type in {"entity", "concept"} and not p.meta.get("sources"):
                no_source.append(p.title)
        orphans = [p.title for p in pages if inbound.get(p.title.lower(), 0) == 0 and p.type != "source"]

        out = ["# Lint report", "", f"{len(pages)} pages checked.", ""]
        out += ["## Broken links", ""] + ([f"- [[{a}]] -> `{b}`" for a, b in broken] or ["- none"]) + [""]
        out += ["## Orphans (no inbound links)", ""] + ([f"- [[{t}]]" for t in orphans] or ["- none"]) + [""]
        out += ["## Missing summary", ""] + ([f"- [[{t}]]" for t in no_summary] or ["- none"]) + [""]
        out += ["## No cited source", ""] + ([f"- [[{t}]]" for t in no_source] or ["- none"]) + [""]

        if use_llm and pages:
            self.index.refresh()
            pairs = self.index.similar_pairs()
            out += ["## Possible duplicates and contradictions", ""]
            found = False
            for a, b, sim in pairs:
                self.echo(f"  comparing [[{a.title}]] vs [[{b.title}]] ({sim:.2f})")
                r = _json(self.llm.complete(self.system, f"""TASK: compare two wiki pages.
duplicate: true if they describe the same subject and should be merged.
contradictions: factual claims that conflict between the pages (empty if none). Quote each claim briefly.

PAGE A:
{a.text()[:6000]}

PAGE B:
{b.text()[:6000]}""", CONTRADICTION_SCHEMA))
                if r["duplicate"]:
                    found = True
                    out.append(f"- Possible duplicate: [[{a.title}]] and [[{b.title}]]")
                for c in r["contradictions"]:
                    found = True
                    out.append(f"- Contradiction between [[{a.title}]] and [[{b.title}]]: "
                               f"\"{c['claim_a']}\" vs \"{c['claim_b']}\" - {c['note']}")
            if not found:
                out.append("- none found")
            out.append("")

            self.echo("  looking for gaps...")
            g = _json(self.llm.complete(self.system, f"""TASK: find gaps in the wiki.
missing_pages: at most 8 important entities or concepts that the pages mention but that have NO page in the INDEX yet.
Each must be a real subject (a proper noun or an established term), not a phrase from a summary.
open_questions: at most 5 questions worth investigating with new sources.

INDEX:
{self.vault.index_text()[:8000]}""", GAPS_SCHEMA))
            missing = [t for t in dict.fromkeys(g["missing_pages"]) if t.strip().lower() not in titles][:8]
            out += ["## Suggested new pages", ""] + ([f"- {t}" for t in missing] or ["- none"]) + [""]
            out += ["## Open questions", ""] + ([f"- {q}" for q in g["open_questions"][:5]] or ["- none"]) + [""]

        report = "\n".join(out)
        (self.vault.wiki / "lint-report.md").write_text(report, encoding="utf-8")
        self.vault.log("lint", f"{len(pages)} pages",
                       f"broken links: {len(broken)}, orphans: {len(orphans)} - see [[lint-report]]")
        return report
