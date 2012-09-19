#!/usr/bin/env python3

import json
import sys

nodes = json.load(sys.stdin)

for node in nodes['nodes']:
  if node['name']:
    for mac in node['macs'].split(','):
      print("%s %s" % (mac.strip(), node['name']))
