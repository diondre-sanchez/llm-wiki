"""MCP server (Streamable HTTP) exposing the wiki to Open WebUI, Claude Desktop, Cursor and other MCP clients.

The client's own model does the reasoning: it searches, reads the pages it needs, and answers.
`wiki_query` is the exception - it runs llm-wiki's configured engine and is opt-in via wiki.toml.

Requires: uv sync --extra mcp
"""

import hmac

import anyio

from .config import Config
from .search import SearchIndex
from .vault import Vault

INSTRUCTIONS = """This server is a personal knowledge wiki: interlinked markdown pages compiled from source documents.
To answer a question from it:
1. Call wiki_search with the question or key terms (or wiki_index to browse every page).
2. Call wiki_read on the most relevant titles - pages are short, so read 2-5 of them.
3. Follow [[links]] inside pages with wiki_read when they look relevant.
4. Answer from the pages only and cite them as [[Page Title]]. If the wiki lacks the answer, say so."""


def build_server(cfg: Config, enable_query: bool):
    from mcp.server.mcpserver import MCPServer

    vault = Vault(cfg)
    vault.ensure()
    index = SearchIndex(cfg, vault)
    server = MCPServer("llm-wiki", instructions=INSTRUCTIONS, log_level="WARNING")

    def _search(query: str, k: int) -> str:
        index.refresh()
        hits = index.search(query, k=max(1, min(k, 20)))
        if not hits:
            return "No pages found. The wiki may be empty."
        return "\n".join(f"- [[{p.title}]] ({p.type}) - {p.summary}" for p, _ in hits)

    def _read(title: str) -> str:
        page = vault.find(title.strip().strip("[]"))
        if page:
            meta = f"type: {page.type} | updated: {page.meta.get('updated', '?')} | sources: {', '.join(page.meta.get('sources', [])) or '-'}"
            return f"{meta}\n\n{page.text()}"
        index.refresh()
        close = ", ".join(f"[[{p.title}]]" for p, _ in index.search(title, k=5))
        return f"No page titled '{title}'. Closest matches: {close or 'none'}"

    @server.tool(description="Hybrid keyword + semantic search over wiki pages. Returns titles and one-line summaries; "
                             "call wiki_read for full text.")
    async def wiki_search(query: str, k: int = 8) -> str:
        return await anyio.to_thread.run_sync(_search, query, k)

    @server.tool(description="Read the full markdown of one wiki page by its exact title (as shown in [[...]]).")
    async def wiki_read(title: str) -> str:
        return await anyio.to_thread.run_sync(_read, title)

    @server.tool(description="The wiki's catalog: every page grouped by type with a one-line summary.")
    async def wiki_index() -> str:
        return vault.index_text() or "The wiki is empty."

    if enable_query:
        from .ops import Wiki
        from .providers import get_llm

        wiki = Wiki(cfg, get_llm(cfg), echo=lambda *_: None)

        @server.tool(description="Ask llm-wiki's own engine to answer a question from the wiki, with [[citations]]. "
                                 "Slower (tens of seconds); prefer wiki_search + wiki_read.")
        async def wiki_query(question: str) -> str:
            return await anyio.to_thread.run_sync(wiki.query, question)

    return server


class BearerAuth:
    """Minimal ASGI middleware: require `Authorization: Bearer <token>` when a token is configured."""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            got = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(got, self.expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"text/plain"), (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b"unauthorized"})
                return
        await self.app(scope, receive, send)


def serve(cfg: Config, host: str | None = None, port: int | None = None) -> None:
    try:
        import uvicorn
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError as e:
        raise SystemExit("The MCP server needs: uv sync --extra mcp") from e

    host = host or cfg.get("mcp", "host", "127.0.0.1")
    port = port or cfg.get("mcp", "port", 8765)
    token = cfg.get("mcp", "token", "")
    enable_query = cfg.get("mcp", "enable_query", False)
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise SystemExit(f"Refusing to listen on {host} without [mcp].token set in wiki.toml - "
                         "the wiki would be readable by anyone on the network.")

    server = build_server(cfg, enable_query)
    if host in {"127.0.0.1", "localhost", "::1"}:
        # Block DNS-rebinding: a web page can't reach a loopback server through another hostname.
        security = TransportSecuritySettings(
            allowed_hosts=[f"{h}:{port}" for h in ("127.0.0.1", "localhost", "[::1]")])
    else:
        # Network-facing: the required bearer token is the protection; clients may use any address.
        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    app = server.streamable_http_app(streamable_http_path="/mcp", host=host, transport_security=security)
    if token:
        app = BearerAuth(app, token)

    tools = "wiki_search, wiki_read, wiki_index" + (", wiki_query" if enable_query else "")
    print(f"llm-wiki MCP server on http://{host}:{port}/mcp  (tools: {tools}; auth: {'bearer token' if token else 'none'})")
    uvicorn.run(app, host=host, port=port, log_level="warning")
