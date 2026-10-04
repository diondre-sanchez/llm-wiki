"""Reading and writing wiki pages: frontmatter, wikilinks, index.md and log.md."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import Config

PAGE_TYPES = {"source": "sources", "entity": "entities", "concept": "concepts", "analysis": "analyses"}
SPECIAL = {"index.md", "log.md", "lint-report.md"}
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


@dataclass
class Page:
    path: Path
    meta: dict = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return self.meta.get("title") or self.path.stem

    @property
    def type(self) -> str:
        return self.meta.get("type", "concept")

    @property
    def summary(self) -> str:
        return self.meta.get("summary", "")

    @property
    def links(self) -> set[str]:
        # Like Obsidian, ignore [[...]] inside fenced code blocks and inline code.
        text = re.sub(r"```.*?```", "", self.body, flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        return {m.strip() for m in WIKILINK.findall(text)}

    def text(self) -> str:
        return f"# {self.title}\n\n{self.body}"


# --- minimal frontmatter (strings and flat lists only; keeps zero dependencies) ---

def _parse_value(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [_unquote(x) for x in _split_list(v[1:-1]) if x.strip()]
    return _unquote(v)


def _split_list(s: str) -> list[str]:
    items, cur, quote = [], "", None
    for ch in s:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == ",":
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    return [i.strip() for i in items]


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1].replace('\\"', '"')
    return v


def _quote(v: str) -> str:
    return '"' + str(v).replace("\n", " ").replace('"', '\\"') + '"'


def parse_page(path: Path) -> Page:
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = raw
    if raw.startswith("---\n"):
        end = raw.find("\n---", 4)
        if end != -1:
            for line in raw[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = _parse_value(v)
            body = raw[end + 4 :].lstrip("\n")
    # Drop a leading H1 that repeats the title; we re-add it on write.
    body = re.sub(r"^# .*\n+", "", body, count=1)
    return Page(path=path, meta=meta, body=body.rstrip() + "\n")


def render_page(page: Page) -> str:
    lines = ["---"]
    for k, v in page.meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(_quote(x) for x in v)}]")
        else:
            lines.append(f"{k}: {_quote(v)}")
    lines.append("---")
    return "\n".join(lines) + f"\n\n# {page.title}\n\n{page.body.strip()}\n"


# --- vault operations ---

def clean_title(title: str) -> str:
    """Make a title usable as both an Obsidian link target and a Windows filename."""
    t = title.replace(": ", " - ").replace(":", "-").replace("/", "-").replace("\\", "-")
    t = re.sub(r'[*?"<>|#^\[\]]', "", t)
    return re.sub(r"\s+", " ", t).strip().rstrip(".")[:120]


def safe_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|#^\[\]]', "", title).strip().rstrip(".")
    return (name or "Untitled")[:120]


class Vault:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.wiki = cfg.wiki_dir
        self.raw = cfg.raw_dir

    def ensure(self) -> None:
        self.raw.mkdir(parents=True, exist_ok=True)
        for sub in PAGE_TYPES.values():
            (self.wiki / sub).mkdir(parents=True, exist_ok=True)
        if not (self.wiki / "index.md").exists():
            self.rebuild_index()
        if not (self.wiki / "log.md").exists():
            (self.wiki / "log.md").write_text("# Log\n\nAppend-only record of wiki operations.\n", encoding="utf-8")

    def pages(self) -> list[Page]:
        return [
            parse_page(p)
            for p in sorted(self.wiki.rglob("*.md"))
            if p.name not in SPECIAL
        ]

    def find(self, title: str) -> Page | None:
        key = title.strip().lower()
        for p in self.pages():
            if p.title.lower() == key or p.path.stem.lower() == key:
                return p
        return None

    def path_for(self, title: str, page_type: str) -> Path:
        return self.wiki / PAGE_TYPES.get(page_type, "concepts") / f"{safe_filename(title)}.md"

    def save(self, title: str, page_type: str, body: str, summary: str,
             sources: list[str] | None = None, tags: list[str] | None = None) -> Page:
        existing = self.find(title)
        now = datetime.now().strftime("%Y-%m-%d")
        meta = dict(existing.meta) if existing else {"title": title, "type": page_type, "created": now}
        meta["title"] = existing.title if existing else title
        meta["summary"] = summary
        meta["updated"] = now
        if sources:
            meta["sources"] = sorted(set(meta.get("sources", [])) | set(sources))
        if tags:
            meta["tags"] = sorted(set(meta.get("tags", [])) | {t.lower().replace(" ", "-") for t in tags})
        path = existing.path if existing else self.path_for(title, page_type)
        page = Page(path=path, meta=meta, body=body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_page(page), encoding="utf-8")
        return page

    def rebuild_index(self) -> None:
        """index.md is generated from frontmatter, so it never drifts from the pages."""
        groups: dict[str, list[Page]] = {t: [] for t in PAGE_TYPES}
        for p in self.pages():
            groups.setdefault(p.type, []).append(p)
        out = ["# Index", "", "Catalog of every wiki page. Generated by `wiki` - do not edit by hand.", ""]
        for t, pages in groups.items():
            if not pages:
                continue
            out.append(f"## {PAGE_TYPES.get(t, t).title()}")
            out.append("")
            for p in sorted(pages, key=lambda x: x.title.lower()):
                out.append(f"- [[{p.title}]] - {p.summary}".rstrip(" -"))
            out.append("")
        (self.wiki / "index.md").write_text("\n".join(out), encoding="utf-8")

    def index_text(self) -> str:
        f = self.wiki / "index.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def log(self, op: str, subject: str, detail: str = "") -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n## [{stamp}] {op} | {subject}\n"
        if detail:
            entry += f"\n{detail.strip()}\n"
        with (self.wiki / "log.md").open("a", encoding="utf-8") as fh:
            fh.write(entry)
