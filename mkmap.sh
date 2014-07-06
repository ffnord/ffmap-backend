#!/bin/bash

set -e

DEST=$1
LOCKFILE="/run/lock/ffmap"

[ "$DEST" ] || exit 1

cd "$(dirname "$0")"/

if lockfile-check "$LOCKFILE"; then
    exit
fi
lockfile-create "$LOCKFILE"
lockfile-touch "$LOCKFILE" &
LOCKPID="$!"

./bat2nodes.py -A -a aliases.json -d $DEST

kill "$LOCKPID"
lockfile-remove "$LOCKFILE"

if lockfile-check "$LOCKFILE-sync"; then
    exit
fi
lockfile-create "$LOCKFILE-sync"
lockfile-touch "$LOCKFILE-sync" &
LOCKPID="$!"

kill "$LOCKPID"
lockfile-remove "$LOCKFILE-sync"
