#!/bin/bash

set -e

DEST=$1


[ "$DEST" ] || exit 1

cd "$(dirname "$0")"/

./ffhlwiki.py http://freifunk.metameute.de/wiki/Knoten > aliases_hl.json
./ffhlwiki.py http://freifunk.metameute.de/wiki/Moelln:Knoten > aliases_moelln.json

./bat2nodes.py -a aliases.json -a aliases_hl.json -a aliases_moelln.json -d $DEST
