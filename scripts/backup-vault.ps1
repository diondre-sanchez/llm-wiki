# Copies the wiki vault (source documents + generated pages) to a backup location, such as an
# external drive. The vault is gitignored, so this is its only backup.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\backup-vault.ps1 -Destination E:\llm-wiki-backup
#   powershell -ExecutionPolicy Bypass -File scripts\backup-vault.ps1 -Destination E:\llm-wiki-backup -Mirror
#
# Set the LLMWIKI_BACKUP environment variable to skip -Destination.
#
# Default: copies new and changed files and never deletes anything at the destination, so files you
# removed from the vault stay in the backup. -Mirror makes the backup an exact copy, deleting files
# from the backup that no longer exist in the vault.
param(
    [string]$Destination = $env:LLMWIKI_BACKUP,
    [switch]$Mirror
)
$ErrorActionPreference = "Stop"

function Fail([string]$message) {
    Write-Host "Backup not done: $message" -ForegroundColor Red
    exit 1
}

if (-not $Destination) {
    Fail "Give -Destination (e.g. E:\llm-wiki-backup) or set the LLMWIKI_BACKUP environment variable."
}
$source = Join-Path (Split-Path -Parent $PSScriptRoot) "vault"
if (-not (Test-Path $source)) { Fail "No vault found at $source" }

$drive = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($Destination))
if ($drive -and -not (Test-Path $drive)) {
    Fail "Drive $drive is not available. Is the external drive plugged in?"
}
$fullSource = (Resolve-Path $source).Path.TrimEnd('\')
$fullDest = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
if ($fullDest -eq $fullSource -or $fullDest.StartsWith("$fullSource\")) {
    Fail "The destination must be outside the vault."
}

$mode = if ($Mirror) { "/MIR" } else { "/E" }
# /XO skips files older than the backup copy; workspace files are Obsidian UI state, not content.
robocopy $fullSource $fullDest $mode /XO /R:1 /W:1 /NP /NDL /NJH `
    /XF "workspace.json" "workspace-mobile.json" | Out-Host

# robocopy exit codes 0-7 mean success (1 = files copied, 0 = already up to date); 8+ is a failure.
if ($LASTEXITCODE -ge 8) {
    Fail "Backup failed (robocopy exit code $LASTEXITCODE)."
}
Write-Host "Vault backed up to $fullDest$(if ($Mirror) { ' (mirrored)' })."
exit 0
