"""Loads wiki.toml from the project root (the nearest parent directory that has one)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    root: Path
    data: dict

    def get(self, section: str, key: str, default=None):
        return self.data.get(section, {}).get(key, default)

    @property
    def provider(self) -> str:
        return self.get("llm", "provider", "ollama")

    @property
    def vault(self) -> Path:
        return self.root / self.get("paths", "vault", "vault")

    @property
    def raw_dir(self) -> Path:
        return self.vault / "raw"

    @property
    def wiki_dir(self) -> Path:
        return self.vault / "wiki"

    @property
    def cache_dir(self) -> Path:
        return self.root / self.get("paths", "cache", ".cache")

    @property
    def schema_text(self) -> str:
        path = self.root / self.get("paths", "schema", "AGENTS.md")
        return path.read_text(encoding="utf-8") if path.exists() else ""


def load_config(start: Path | None = None) -> Config:
    here = (start or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        f = d / "wiki.toml"
        if f.exists():
            with f.open("rb") as fh:
                return Config(root=d, data=tomllib.load(fh))
    raise SystemExit("wiki.toml not found in this directory or any parent.")
