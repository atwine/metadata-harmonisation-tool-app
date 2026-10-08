#!/usr/bin/env bash
# Back up ./harmonisation-data into harmonisation-backups/mht-backup-<date>.tar.gz
# Usage (run from the folder that holds the compose file):
#   ./scripts/backup.sh [compose-file]      default: docker-compose.yml
# The backend is stopped while copying so the SQLite database (which uses WAL
# mode) is copied in a consistent state, then started again.
set -euo pipefail

COMPOSE="${1:-docker-compose.yml}"
DATA="harmonisation-data"
OUT_DIR="harmonisation-backups"

[ -d "$DATA" ] || { echo "No ./$DATA folder here. Run this from the folder with $COMPOSE." >&2; exit 1; }

was_running=""
if command -v docker >/dev/null 2>&1 && [ -n "$(docker compose -f "$COMPOSE" ps --status running -q backend 2>/dev/null)" ]; then
  was_running=1
  echo "Stopping the backend for a consistent copy..."
  docker compose -f "$COMPOSE" stop backend >/dev/null
else
  echo "Backend not running (or Docker not found): copying as is. Make sure the app is not in use."
fi
restart() { [ -z "$was_running" ] || { echo "Starting the backend again..."; docker compose -f "$COMPOSE" up -d --no-deps backend >/dev/null; }; }
trap restart EXIT

mkdir -p "$OUT_DIR"
archive="$OUT_DIR/mht-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$archive" "$DATA"
tar -tzf "$archive" >/dev/null
echo "Backup written: $archive ($(du -h "$archive" | cut -f1))"
echo "It contains participant data. Keep it somewhere private; never commit or share it."
