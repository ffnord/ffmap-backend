#!/bin/bash

set -e

DEST=$1


[ "$DEST" ] || exit 1

"$(dirname "$0")"/ffhlwiki.py http://freifunk.metameute.de/wiki/Knoten > "$(dirname "$0")"/aliases_hl.json
"$(dirname "$0")"/ffhlwiki.py http://freifunk.metameute.de/wiki/Moelln:Knoten > "$(dirname "$0")"/aliases_moelln.json

"$(dirname "$0")"/bat2nodes.py -a "$(dirname "$0")"/aliases.json -a aliases_hl.json -a aliases_moelln.json > $DEST/nodes.json.new

mv $DEST/nodes.json.new $DEST/nodes.json

