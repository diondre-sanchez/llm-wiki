# Starts the llm-wiki MCP server from the repo root (settings come from wiki.toml [mcp]).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\start-mcp.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
uv run wiki mcp @args
