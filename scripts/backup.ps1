# Back up .\harmonisation-data into harmonisation-backups\mht-backup-<date>.tar.gz
# Usage (PowerShell, from the folder that holds the compose file):
#   .\scripts\backup.ps1 [-ComposeFile docker-compose.yml]
# The backend is stopped while copying so the SQLite database (WAL mode) is
# copied in a consistent state, then started again.
param([string]$ComposeFile = "docker-compose.yml")
$ErrorActionPreference = "Stop"
$Data = "harmonisation-data"
$OutDir = "harmonisation-backups"

if (-not (Test-Path $Data)) { throw "No .\$Data folder here. Run this from the folder with $ComposeFile." }

$wasRunning = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $wasRunning = [bool](docker compose -f $ComposeFile ps --status running -q backend 2>$null)
}
try {
  if ($wasRunning) {
    Write-Host "Stopping the backend for a consistent copy..."
    docker compose -f $ComposeFile stop backend | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not stop the backend, so no backup was made (copying a running database is not safe)." }
  } else {
    Write-Host "Backend not running (or Docker not found): copying as is. Make sure the app is not in use."
  }
  New-Item -ItemType Directory -Force $OutDir | Out-Null
  $archive = Join-Path $OutDir ("mht-backup-{0}.tar.gz" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
  tar -czf $archive $Data
  if ($LASTEXITCODE -ne 0) { throw "tar failed" }
  tar -tzf $archive | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "backup could not be read back" }
  Write-Host ("Backup written: {0} ({1:N1} MB)" -f $archive, ((Get-Item $archive).Length / 1MB))
  Write-Host "It contains participant data. Keep it somewhere private; never commit or share it."
} finally {
  if ($wasRunning) {
    Write-Host "Starting the backend again..."
    docker compose -f $ComposeFile up -d --no-deps backend | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Warning "The backend did not start. Run: docker compose -f $ComposeFile up -d backend" }
  }
}
