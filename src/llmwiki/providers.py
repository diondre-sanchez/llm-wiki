"""LLM and embedding providers.

Every LLM backend implements one method: complete(system, prompt, schema=None) -> str.
When `schema` (a JSON Schema dict) is given, the backend constrains output to valid JSON
matching it and returns the raw JSON text. Embeddings always come from local Ollama.
"""

import json
import urllib.error
import urllib.request
from typing import Protocol

from .config import Config


class LLM(Protocol):
    name: str

    def complete(self, system: str, prompt: str, schema: dict | None = None) -> str: ...


def _post_json(url: str, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama request failed ({e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach Ollama at {url}: {e.reason}. Is `ollama serve` running?") from e


class OllamaLLM:
    def __init__(self, cfg: Config):
        self.host = cfg.get("ollama", "host", "http://localhost:11434").rstrip("/")
        self.model = cfg.get("ollama", "model", "qwen3.8:27b")
        self.num_ctx = cfg.get("ollama", "num_ctx", 16384)
        self.temperature = cfg.get("ollama", "temperature", 0.2)
        self.think = cfg.get("ollama", "think", False)
        self.timeout = cfg.get("ollama", "timeout", 900)
        self.name = f"ollama:{self.model}"

    def complete(self, system: str, prompt: str, schema: dict | None = None) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": self.think,
            "options": {"num_ctx": self.num_ctx, "temperature": self.temperature},
        }
        if schema:
            body["format"] = schema
        data = _post_json(f"{self.host}/api/chat", body, self.timeout)
        return data["message"]["content"].strip()


class AnthropicLLM:
    def __init__(self, cfg: Config):
        try:
            import anthropic
        except ImportError as e:
            raise SystemExit("Claude provider needs the SDK: uv sync --extra claude") from e
        self.client = anthropic.Anthropic()
        self.model = cfg.get("anthropic", "model", "claude-opus-5-5")
        self.effort = cfg.get("anthropic", "effort", "medium")
        self.max_tokens = cfg.get("anthropic", "max_tokens", 32000)
        self.name = f"anthropic:{self.model}"

    def complete(self, system: str, prompt: str, schema: dict | None = None) -> str:
        output_config: dict = {"effort": self.effort}
        if schema:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        # The schema/system prompt is identical across calls, so cache it.
        # Server-side fallbacks re-run a refused request on another model automatically.
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
            output_config=output_config,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {msg.stop_details}")
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("Claude hit max_tokens; raise [anthropic].max_tokens in wiki.toml")
        return "".join(b.text for b in msg.content if b.type == "text").strip()


def get_llm(cfg: Config, provider: str | None = None) -> LLM:
    provider = provider or cfg.provider
    if provider == "ollama":
        return OllamaLLM(cfg)
    if provider == "anthropic":
        return AnthropicLLM(cfg)
    raise SystemExit(f"Unknown provider '{provider}' (expected 'ollama' or 'anthropic')")


class Embedder:
    """Local embeddings via Ollama. nomic-embed-text expects task prefixes."""

    def __init__(self, cfg: Config):
        self.host = cfg.get("embeddings", "host", "http://localhost:11434").rstrip("/")
        self.model = cfg.get("embeddings", "model", "nomic-embed-text")
        self._prefix = self.model.startswith("nomic-embed")

    def _embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 16):
            data = _post_json(
                f"{self.host}/api/embed",
                {"model": self.model, "input": texts[i : i + 16], "truncate": True},
                timeout=300,
            )
            out.extend(data["embeddings"])
        return out

    def documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed([f"search_document: {t}" if self._prefix else t for t in texts])

    def query(self, text: str) -> list[float]:
        return self._embed([f"search_query: {text}" if self._prefix else text])[0]
