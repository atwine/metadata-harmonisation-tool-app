#!/bin/sh
# Starts as root only long enough to make the data folders writable, then runs
# the app as an ordinary user.
#
# Why: the data folders are bind mounts from the researcher's computer. On Linux
# Docker creates a missing host folder owned by root, which an ordinary user
# could not write to. Here, a folder owned by root (or by this image's own app
# user left over from an earlier run) is handed to the app user. A folder the
# researcher already owns is left alone and the app runs as that same user, so
# the files stay editable on the host.
set -e

if [ "$(id -u)" != "0" ]; then
  exec "$@"
fi

DIRS="db input results logs ontology_cache"
DEFAULT_UID=10001
APP_UID=$DEFAULT_UID
APP_GID=$DEFAULT_UID

for d in $DIRS; do
  mkdir -p "/app/$d"
done

# The first folder owned by a real person decides who the app runs as.
for d in $DIRS; do
  owner="$(stat -c %u "/app/$d")"
  if [ "$owner" != "0" ] && [ "$owner" != "$DEFAULT_UID" ]; then
    APP_UID="$owner"
    APP_GID="$(stat -c %g "/app/$d")"
    break
  fi
done

# Hand over only folders nobody real owns. A failure (a read-only mount, or a
# network drive that refuses root) is a warning, not a crash: if the app user
# can already write there, the app still works.
for d in $DIRS; do
  owner="$(stat -c %u "/app/$d")"
  if [ "$owner" = "0" ] || { [ "$owner" = "$DEFAULT_UID" ] && [ "$APP_UID" != "$DEFAULT_UID" ]; }; then
    chown -R "$APP_UID:$APP_GID" "/app/$d" \
      || echo "warning: could not change the owner of /app/$d; continuing" >&2
  fi
done

exec gosu "$APP_UID:$APP_GID" "$@"
