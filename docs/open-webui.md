# Using llm-wiki from Open WebUI

llm-wiki runs a small MCP server. Open WebUI connects to it as an external tool server, and the
chat model you pick in Open WebUI searches and reads wiki pages before answering.

```
browser / phone ──► Open WebUI ──(backend)──► llm-wiki MCP  http://127.0.0.1:8765/mcp
```

Open WebUI's backend makes the tool calls, not the browser. The MCP server can therefore stay on
`127.0.0.1` even when you use Open WebUI from other devices through a reverse proxy: nothing about
Caddy or your network needs to change.

Requires Open WebUI 0.6.31 or newer (native MCP support).

## 1. Start the server

```bash
uv sync --extra convert --extra mcp
```

```bash
uv run wiki mcp
```

It prints `llm-wiki MCP server on http://127.0.0.1:8765/mcp`. Leave it running.

To start it automatically at logon on Windows, run once from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-startup-task.ps1
```

## 2. Connect Open WebUI

1. Open **Admin Panel → Settings → Integrations**.
2. Under **External Tool Servers** (called **Tool Servers** in some versions), click **+ Add Connection**.
3. Set **Type** to **MCP (Streamable HTTP)**.
4. Set **URL** to `http://127.0.0.1:8765/mcp`.
5. Set **Auth** to **None**, or **Bearer** with your token if you set `[mcp].token` in `wiki.toml`.
6. Save. The connection should verify, and the tools appear as `wiki_search`, `wiki_read` and `wiki_index`.

If Open WebUI runs in Docker instead of natively, use `http://host.docker.internal:8765/mcp` and start
the server with `--host 0.0.0.0` and a token (see Security).

## 3. Set up the model

1. **Workspace → Models**, edit the model you chat with (e.g. `qwen3.8:27b`), or create a wrapper
   model called something like "Wiki assistant".
2. Under **Advanced Params**, set **Function Calling** to **Native**.
3. Under **Tools**, tick the llm-wiki tools so they are on by default. Otherwise enable them per chat
   from the **+ / Integrations** menu in the message box.
4. Optional system prompt:

   > You have a personal knowledge wiki. For questions it might cover, call wiki_search, then wiki_read
   > on the most relevant pages, and answer from them, citing pages as [[Page Title]]. Say so when the
   > wiki doesn't cover something.

Use a model with solid tool calling. Small models often skip the tools or call them with bad arguments.

## Tools

| Tool | What it returns |
|---|---|
| `wiki_search(query, k=8)` | Hybrid keyword + semantic search: page titles and one-line summaries |
| `wiki_read(title)` | Full markdown of one page, with its type, update date and sources. Suggests close matches if the title is wrong |
| `wiki_index()` | The catalog of every page |
| `wiki_query(question)` | Off by default. Answers with llm-wiki's own engine; set `[mcp].enable_query = true` |

The tools are read-only. Add sources with `uv run wiki ingest` in a terminal; new pages are searchable
from Open WebUI immediately, without restarting the server.

## Security

- The default bind address `127.0.0.1` is only reachable from this machine, and DNS-rebinding
  protection blocks web pages from reaching it through another hostname.
- To expose the server on the network (Docker, or another machine), set `[mcp].token` in `wiki.toml`
  and start it with `--host 0.0.0.0`. The server refuses to listen on a non-loopback address without a token.
- Don't route the MCP port through Caddy or your router. Clients reach the wiki through Open WebUI.

## Other MCP clients

The same server works with any MCP client that supports Streamable HTTP, such as Claude Desktop,
Claude Code (`claude mcp add --transport http llm-wiki http://127.0.0.1:8765/mcp`) and Cursor.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Connection fails to verify | Check `uv run wiki mcp` is running, and the URL ends in `/mcp` |
| `421 Misdirected Request` | The URL's host isn't allowed. Use `127.0.0.1` or `localhost` with the loopback default |
| `401 Unauthorized` | Token mismatch between Open WebUI's Bearer field and `[mcp].token` |
| Model never calls the tools | Set Function Calling to Native, enable the tools for the chat, or try a stronger model |
| Searches are slow the first time | Embeddings for changed pages are computed on the first search after an ingest |
