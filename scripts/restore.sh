#!/usr/bin/env bash
# Restore ./harmonisation-data from a backup made by scripts/backup.sh
# Usage (run from the folder that holds the compose file):
#   ./scripts/restore.sh <backup.tar.gz> [compose-file]
# Nothing is deleted: the current data folder is renamed to
# harmonisation-data.before-restore-<date> so you can undo the restore.
set -euo pipefail

ARCHIVE="${1:?Usage: ./scripts/restore.sh <backup.tar.gz> [compose-file]}"
COMPOSE="${2:-docker-compose.yml}"
DATA="harmonisation-data"

[ -f "$ARCHIVE" ] || { echo "Backup not found: $ARCHIVE" >&2; exit 1; }
tar -tzf "$ARCHIVE" | grep "^$DATA/" >/dev/null || { echo "$ARCHIVE does not look like an MHT backup." >&2; exit 1; }

was_running=""
if command -v docker >/dev/null 2>&1 && [ -n "$(docker compose -f "$COMPOSE" ps --status running -q backend 2>/dev/null)" ]; then
  was_running=1
  echo "Stopping the backend..."
  docker compose -f "$COMPOSE" stop backend >/dev/null
else
  echo "Backend not running (or Docker not found). Make sure the app is not in use."
fi
restart() { [ -z "$was_running" ] || { echo "Starting the backend again..."; docker compose -f "$COMPOSE" up -d --no-deps backend >/dev/null; }; }
trap restart EXIT

if [ -e "$DATA" ]; then
  saved="$DATA.before-restore-$(date +%Y%m%d-%H%M%S)"
  mv "$DATA" "$saved"
  echo "Current data kept at: $saved"
fi
tar -xzf "$ARCHIVE"
echo "Restored from $ARCHIVE"
