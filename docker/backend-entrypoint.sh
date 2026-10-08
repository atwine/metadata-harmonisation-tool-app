#!/bin/sh
# Starts as root only long enough to make the data folders writable, then runs
# the app as an ordinary user.
#
# Why: the data folders are bind mounts from the researcher's computer. On Linux
# Docker creates a missing host folder owned by root, which an ordinary user
# could not write to. Here, a root-owned folder is handed to the app user; a
# folder the researcher already owns is left alone and the app runs as that
# same user, so the files stay editable on the host.
set -e

if [ "$(id -u)" != "0" ]; then
  exec "$@"
fi

APP_UID=10001
APP_GID=10001

# The first folder owned by someone other than root decides who the app runs as.
for d in db input results logs ontology_cache; do
  mkdir -p "/app/$d"
  owner="$(stat -c %u "/app/$d")"
  if [ "$owner" != "0" ]; then
    APP_UID="$owner"
    APP_GID="$(stat -c %g "/app/$d")"
    break
  fi
done

for d in db input results logs ontology_cache; do
  if [ "$(stat -c %u "/app/$d")" = "0" ]; then
    chown -R "$APP_UID:$APP_GID" "/app/$d"
  fi
done

exec gosu "$APP_UID:$APP_GID" "$@"
