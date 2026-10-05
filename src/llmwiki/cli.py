"""Command line entry point: `wiki <command>`."""

import argparse
import sys
import time
from pathlib import Path

from .config import load_config
from .providers import Embedder, get_llm
from .search import SearchIndex
from .sources import UnsupportedSource, is_supported
from .vault import Vault


def _expand(paths: list[str]) -> list[Path]:
    out, skipped = [], []
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(x for x in p.rglob("*") if x.is_file() and not x.name.startswith(".")):
                (out if is_supported(f) else skipped).append(f)
        elif p.exists():
            out.append(p)  # named explicitly: let read_source explain if it can't be read
        else:
            print(f"skip (not found): {p}", file=sys.stderr)
    if skipped:
        names = ", ".join(f.name for f in skipped[:5]) + (" ..." if len(skipped) > 5 else "")
        print(f"skip ({len(skipped)} unsupported): {names}", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(prog="wiki", description="Local LLM-maintained markdown wiki.")
    ap.add_argument("--provider", choices=["ollama", "anthropic"], help="override [llm].provider for this run")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create the vault folders, index.md and log.md")
    sub.add_parser("status", help="show config and check that models are reachable")

    p = sub.add_parser("ingest", help="compile sources into wiki pages")
    p.add_argument("paths", nargs="+", help="files or folders (md, txt, pdf, html)")

    p = sub.add_parser("query", help="ask the wiki a question")
    p.add_argument("question")
    p.add_argument("-k", type=int, help="number of pages to retrieve")
    p.add_argument("--save", action="store_true", help="file the answer back into the wiki as an analysis page")

    p = sub.add_parser("search", help="hybrid search without calling the LLM")
    p.add_argument("text")
    p.add_argument("-k", type=int, default=10)

    p = sub.add_parser("lint", help="health-check the wiki")
    p.add_argument("--no-llm", action="store_true", help="structural checks only")

    sub.add_parser("reindex", help="rebuild index.md and refresh embeddings")

    p = sub.add_parser("mcp", help="serve the wiki to MCP clients (Open WebUI, Claude Desktop, ...) over HTTP")
    p.add_argument("--host", help="bind address (default [mcp].host, 127.0.0.1)")
    p.add_argument("--port", type=int, help="port (default [mcp].port, 8765)")

    args = ap.parse_args(argv)
    cfg = load_config()

    if args.cmd == "init":
        Vault(cfg).ensure()
        print(f"Vault ready at {cfg.vault}. Open that folder in Obsidian.")
        return

    if args.cmd == "status":
        llm = get_llm(cfg, args.provider)
        print(f"root:       {cfg.root}")
        print(f"vault:      {cfg.vault}  ({len(Vault(cfg).pages())} pages)")
        print(f"engine:     {llm.name}")
        print(f"embeddings: ollama:{Embedder(cfg).model}")
        t = time.time()
        print("ping llm:  ", llm.complete("Reply with exactly: ok", "ping")[:40], f"({time.time() - t:.1f}s)")
        print("ping embed:", f"{len(Embedder(cfg).query('ping'))} dims")
        return

    if args.cmd == "search":
        vault = Vault(cfg)
        vault.ensure()
        idx = SearchIndex(cfg, vault)
        idx.refresh()
        for page, score in idx.search(args.text, k=args.k):
            print(f"{score:.4f}  [[{page.title}]] ({page.type}) - {page.summary}")
        return

    if args.cmd == "reindex":
        vault = Vault(cfg)
        vault.ensure()
        vault.rebuild_index()
        n = SearchIndex(cfg, vault).refresh()
        print(f"index.md rebuilt; {n} page(s) re-embedded.")
        return

    if args.cmd == "mcp":
        from .mcp_server import serve

        serve(cfg, host=args.host, port=args.port)
        return

    from .ops import Wiki

    wiki = Wiki(cfg, get_llm(cfg, args.provider))

    if args.cmd == "ingest":
        files = _expand(args.paths)
        failed = []
        for i, f in enumerate(files, 1):
            print(f"[{i}/{len(files)}] ingesting {f.name} with {wiki.llm.name}")
            t = time.time()
            try:
                touched = wiki.ingest(f)
            except UnsupportedSource as e:
                print(f"  skipped: {e}", file=sys.stderr)
                failed.append(f.name)
                continue
            except RuntimeError as e:  # model errors: context overflow, invalid JSON, Ollama unreachable
                print(f"  failed: {e}\n  Condensed notes are cached, so re-running resumes quickly.", file=sys.stderr)
                failed.append(f.name)
                continue
            print(f"  done in {time.time() - t:.0f}s - {len(touched)} pages: {', '.join(touched)}")
        if failed:
            print(f"{len(failed)} of {len(files)} file(s) not ingested: {', '.join(failed)}", file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "query":
        print(wiki.query(args.question, k=args.k, save=args.save))
    elif args.cmd == "lint":
        print(wiki.lint(use_llm=not args.no_llm))


if __name__ == "__main__":
    main()
