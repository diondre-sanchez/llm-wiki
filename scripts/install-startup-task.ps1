# Registers a Windows scheduled task that starts the llm-wiki MCP server when you log on,
# so it is always available to Open WebUI. Remove it with:
#   Unregister-ScheduledTask -TaskName "llm-wiki MCP" -Confirm:$false
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "start-mcp.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "llm-wiki MCP" -Action $action -Trigger $trigger -Settings $settings `
    -Description "llm-wiki MCP server for Open WebUI" -Force | Out-Null
Start-ScheduledTask -TaskName "llm-wiki MCP"
Write-Host "Registered and started 'llm-wiki MCP'. It will start automatically at logon."
