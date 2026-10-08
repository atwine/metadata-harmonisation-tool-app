# Restore .\harmonisation-data from a backup made by scripts\backup.ps1 (or backup.sh)
# Usage (PowerShell, from the folder that holds the compose file):
#   .\scripts\restore.ps1 -Archive harmonisation-backups\mht-backup-<date>.tar.gz [-ComposeFile docker-compose.yml]
# Nothing is deleted: the current data folder is renamed to
# harmonisation-data.before-restore-<date> so you can undo the restore.
param([Parameter(Mandatory = $true)][string]$Archive, [string]$ComposeFile = "docker-compose.yml")
$ErrorActionPreference = "Stop"
$Data = "harmonisation-data"

if (-not (Test-Path $Archive)) { throw "Backup not found: $Archive" }
if (-not ((tar -tzf $Archive) -match "^$Data/")) { throw "$Archive does not look like an MHT backup." }

$wasRunning = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $wasRunning = [bool](docker compose -f $ComposeFile ps --status running -q backend 2>$null)
}
if ($wasRunning) { Write-Host "Stopping the backend..."; docker compose -f $ComposeFile stop backend | Out-Null }
else { Write-Host "Backend not running (or Docker not found). Make sure the app is not in use." }
try {
  if (Test-Path $Data) {
    $saved = "$Data.before-restore-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
    Rename-Item $Data $saved
    Write-Host "Current data kept at: $saved"
  }
  tar -xzf $Archive
  if ($LASTEXITCODE -ne 0) { throw "tar failed" }
  Write-Host "Restored from $Archive"
} finally {
  if ($wasRunning) { Write-Host "Starting the backend again..."; docker compose -f $ComposeFile up -d --no-deps backend | Out-Null }
}
