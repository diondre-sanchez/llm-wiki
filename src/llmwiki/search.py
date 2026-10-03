"""Hybrid retrieval over wiki pages: BM25 keyword scores + local embeddings, fused with RRF.

This is the "RAG" half of the system, but it retrieves compiled wiki pages rather than raw chunks.
Embeddings are cached in .cache/embeddings.json and only recomputed when a page changes.
"""

import hashlib
import json
import math
import re
from collections import Counter

from .config import Config
from .providers import Embedder
from .vault import Page, Vault

TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were will with".split())
EMBED_CHARS = 6000


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 1]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class SearchIndex:
    def __init__(self, cfg: Config, vault: Vault):
        self.cfg = cfg
        self.vault = vault
        self.embedder = Embedder(cfg)
        self.cache_file = cfg.cache_dir / "embeddings.json"
        self.pages: list[Page] = []
        self.vectors: dict[str, list[float]] = {}

    def _key(self, p: Page) -> str:
        return p.path.relative_to(self.vault.wiki).as_posix()

    def refresh(self) -> int:
        """Load pages and embed any that are new or changed. Returns the number re-embedded."""
        self.pages = self.vault.pages()
        cache = {}
        if self.cache_file.exists():
            cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
        if cache.get("model") != self.embedder.model:
            cache = {"model": self.embedder.model, "items": {}}
        items = cache["items"]

        todo = []
        for p in self.pages:
            text = p.text()[:EMBED_CHARS]
            digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
            k = self._key(p)
            if items.get(k, {}).get("hash") != digest:
                todo.append((k, digest, text))
        if todo:
            vecs = self.embedder.documents([t for _, _, t in todo])
            for (k, digest, _), v in zip(todo, vecs):
                items[k] = {"hash": digest, "vec": v}

        live = {self._key(p) for p in self.pages}
        cache["items"] = {k: v for k, v in items.items() if k in live}
        self.cfg.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(cache), encoding="utf-8")
        self.vectors = {k: v["vec"] for k, v in cache["items"].items()}
        return len(todo)

    def _bm25(self, query: str, k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
        docs = {self._key(p): tokenize(f"{p.title} {p.title} {p.summary} {p.body}") for p in self.pages}
        if not docs:
            return {}
        avgdl = sum(len(d) for d in docs.values()) / len(docs)
        df = Counter(t for d in docs.values() for t in set(d))
        n = len(docs)
        scores = {}
        q = tokenize(query)
        for key, toks in docs.items():
            tf = Counter(toks)
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(toks) / avgdl))
            if s > 0:
                scores[key] = s
        return scores

    def search(self, query: str, k: int = 6, types: set[str] | None = None) -> list[tuple[Page, float]]:
        if not self.pages:
            self.refresh()
        pool = [p for p in self.pages if not types or p.type in types]
        if not pool:
            return []
        by_key = {self._key(p): p for p in pool}

        bm = self._bm25(query)
        qv = self.embedder.query(query)
        dense = {key: cosine(qv, self.vectors[key]) for key in by_key if key in self.vectors}

        # Reciprocal rank fusion: robust to the two scorers having different scales.
        fused: Counter = Counter()
        for ranking in (bm, dense):
            ordered = sorted((key for key in ranking if key in by_key), key=lambda x: -ranking[x])
            for rank, key in enumerate(ordered):
                fused[key] += 1.0 / (60 + rank)
        return [(by_key[key], score) for key, score in fused.most_common(k)]

    def similar_pairs(self, threshold: float = 0.82, limit: int = 10) -> list[tuple[Page, Page, float]]:
        """Most similar page pairs - the likeliest places for duplicates or contradictions."""
        if not self.pages:
            self.refresh()
        keyed = [(self._key(p), p) for p in self.pages if self._key(p) in self.vectors and p.type != "source"]
        pairs = []
        for i in range(len(keyed)):
            for j in range(i + 1, len(keyed)):
                s = cosine(self.vectors[keyed[i][0]], self.vectors[keyed[j][0]])
                if s >= threshold:
                    pairs.append((keyed[i][1], keyed[j][1], s))
        return sorted(pairs, key=lambda x: -x[2])[:limit]
