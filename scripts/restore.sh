#!/usr/bin/env bash
# Restore ./harmonisation-data from a backup made by scripts/backup.sh
# Usage (run from the folder that holds the compose file):
#   ./scripts/restore.sh <backup.tar.gz> [compose-file]
# Nothing is deleted: the current data folder is renamed to
# harmonisation-data.before-restore-<date> so you can undo the restore.
# The backup is unpacked into a temporary folder first, so a damaged or
# oversized archive cannot leave you with half a data folder.
set -euo pipefail

ARCHIVE="${1:?Usage: ./scripts/restore.sh <backup.tar.gz> [compose-file]}"
COMPOSE="${2:-docker-compose.yml}"
DATA="harmonisation-data"

[ -f "$ARCHIVE" ] || { echo "Backup not found: $ARCHIVE" >&2; exit 1; }

# Every entry must live under harmonisation-data/ and none may climb out of it.
entries="$(tar -tzf "$ARCHIVE")" || { echo "$ARCHIVE could not be read." >&2; exit 1; }
if [ -z "$entries" ] \
   || printf '%s\n' "$entries" | grep -v "^$DATA/" | grep -q . \
   || printf '%s\n' "$entries" | grep -Eq '(^|/)\.\.(/|$)'; then
  echo "$ARCHIVE does not look like an MHT backup (unexpected files inside). Nothing was changed." >&2
  exit 1
fi

was_running=""
tmp=""
restart() {
  [ -z "$tmp" ] || rm -rf -- "$tmp"
  [ -z "$was_running" ] || { echo "Starting the backend again..."; docker compose -f "$COMPOSE" up -d --no-deps backend >/dev/null; }
}
trap restart EXIT

if command -v docker >/dev/null 2>&1 && [ -n "$(docker compose -f "$COMPOSE" ps --status running -q backend 2>/dev/null)" ]; then
  was_running=1
  echo "Stopping the backend..."
  docker compose -f "$COMPOSE" stop backend >/dev/null
else
  echo "Backend not running (or Docker not found). Make sure the app is not in use."
fi

tmp="$(mktemp -d "./$DATA.restore-tmp.XXXXXX")"
tar -xzf "$ARCHIVE" -C "$tmp"
[ -d "$tmp/$DATA" ] || { echo "$ARCHIVE has no $DATA folder. Nothing was changed." >&2; exit 1; }

if [ -e "$DATA" ]; then
  saved="$DATA.before-restore-$(date +%Y%m%d-%H%M%S)"
  mv "$DATA" "$saved"
  echo "Current data kept at: $saved"
fi
mv "$tmp/$DATA" "$DATA"
echo "Restored from $ARCHIVE"
