#!/bin/sh
# Starts as root only long enough to make the data folders writable, then runs
# the app as an ordinary user.
#
# Why: the data folders are bind mounts from the researcher's computer. On Linux
# Docker creates a missing host folder owned by root, which an ordinary user
# could not write to. Here, anything inside a data folder owned by root (or by
# this image's own app user, from an earlier run) is handed to the app user. A
# folder the researcher already owns keeps its owner and the app runs as that
# same user, so the files stay editable on the host.
set -e

if [ "$(id -u)" != "0" ]; then
  exec "$@"
fi

# Rootless Docker and Podman: "root" in the container is the researcher's own
# user on the host. Changing owners there would hand their files to a stranger
# uid, so leave everything as it is and run the app as that user.
if [ -r /proc/self/uid_map ]; then
  uid_map="$(head -n 1 /proc/self/uid_map | tr -s ' \t' '  ' | sed 's/^ //; s/ $//')"
  if [ "$uid_map" != "0 0 4294967295" ]; then
    exec "$@"
  fi
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

# Hand over only what nobody real owns: entries owned by root, or by this
# image's app user when a person now owns the folders. Files owned by anyone else
# are left alone. A failure (a read-only mount, or a network drive that refuses
# root) is a warning, not a crash: if the app user can already write there, the
# app still works.
for d in $DIRS; do
  if [ -n "$(find "/app/$d" \( -uid 0 -o -uid "$DEFAULT_UID" \) ! -uid "$APP_UID" -print -quit)" ]; then
    find "/app/$d" \( -uid 0 -o -uid "$DEFAULT_UID" \) ! -uid "$APP_UID" -exec chown -h "$APP_UID:$APP_GID" {} + \
      || echo "warning: could not change the owner of everything in /app/$d; continuing" >&2
  fi
done

exec gosu "$APP_UID:$APP_GID" "$@"
