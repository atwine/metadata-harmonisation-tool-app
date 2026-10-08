# Restore .\harmonisation-data from a backup made by scripts\backup.ps1 (or backup.sh)
# Usage (PowerShell, from the folder that holds the compose file):
#   .\scripts\restore.ps1 -Archive harmonisation-backups\mht-backup-<date>.tar.gz [-ComposeFile docker-compose.yml]
# Nothing is deleted: the current data folder is renamed to
# harmonisation-data.before-restore-<date> so you can undo the restore.
# The backup is unpacked into a temporary folder first, so a damaged or
# oversized archive cannot leave you with half a data folder.
param([Parameter(Mandatory = $true)][string]$Archive, [string]$ComposeFile = "docker-compose.yml")
$ErrorActionPreference = "Stop"
$Data = "harmonisation-data"

if (-not (Test-Path $Archive)) { throw "Backup not found: $Archive" }

# Every entry must live under harmonisation-data/ and none may climb out of it.
$entries = @(tar -tzf $Archive)
if ($LASTEXITCODE -ne 0) { throw "$Archive could not be read." }
$unexpected = @($entries | Where-Object { -not $_.StartsWith("$Data/") -or $_ -match '(^|/)\.\.(/|$)' })
if ($entries.Count -eq 0 -or $unexpected.Count -gt 0) {
  throw "$Archive does not look like an MHT backup (unexpected files inside). Nothing was changed."
}

$wasRunning = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $wasRunning = [bool](docker compose -f $ComposeFile ps --status running -q backend 2>$null)
}
$tmp = $null
try {
  if ($wasRunning) {
    Write-Host "Stopping the backend..."
    docker compose -f $ComposeFile stop backend | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not stop the backend. Nothing was changed." }
  } else {
    Write-Host "Backend not running (or Docker not found). Make sure the app is not in use."
  }
  $tmp = Join-Path (Get-Location) ("$Data.restore-tmp." + [guid]::NewGuid().ToString("N").Substring(0, 8))
  New-Item -ItemType Directory $tmp | Out-Null
  tar -xzf $Archive -C $tmp
  if ($LASTEXITCODE -ne 0) { throw "tar failed. Nothing was changed." }
  if (-not (Test-Path (Join-Path $tmp $Data))) { throw "$Archive has no $Data folder. Nothing was changed." }
  if (Test-Path $Data) {
    $saved = "$Data.before-restore-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
    Rename-Item $Data $saved
    Write-Host "Current data kept at: $saved"
  }
  Move-Item (Join-Path $tmp $Data) $Data
  Write-Host "Restored from $Archive"
} finally {
  if ($tmp -and (Test-Path $tmp)) { Remove-Item -Recurse -Force $tmp }
  if ($wasRunning) {
    Write-Host "Starting the backend again..."
    docker compose -f $ComposeFile up -d --no-deps backend | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Warning "The backend did not start. Run: docker compose -f $ComposeFile up -d backend" }
  }
}
