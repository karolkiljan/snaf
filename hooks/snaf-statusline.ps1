# snaf — statusline badge (Windows/PowerShell)
# Reads ~/.claude/.snaf-active flag and prints [SNAF] when active.
# Add to ~/.claude/settings.json:
#   "statusLine": { "type": "command", "command": "powershell -ExecutionPolicy Bypass -File /path/to/snaf-statusline.ps1" }

$flagPath = Join-Path $HOME ".claude\.snaf-active"

if (Test-Path $flagPath) {
  Write-Output "[SNAF]"
}
