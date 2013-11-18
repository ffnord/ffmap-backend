#!/usr/bin/env python3

import json
import fileinput
import argparse
import os

from rrd import rrd
from nodedb import NodeDB
from d3mapbuilder import D3MapBuilder

# Force encoding to UTF-8
import locale                                  # Ensures that subsequent open()s
locale.getpreferredencoding = lambda _=None: 'UTF-8'  # are UTF-8 encoded.

import sys
#sys.stdin = open('/dev/stdin', 'r')
#sys.stdout = open('/dev/stdout', 'w')
#sys.stderr = open('/dev/stderr', 'w')

parser = argparse.ArgumentParser()

parser.add_argument('-a', '--aliases',
                  help='read aliases from FILE',
                  action='append',
                  metavar='FILE')

parser.add_argument('-g', '--gateway', action='append',
                  help='MAC of a gateway')

parser.add_argument('batmanjson', help='output of batman vd json')

parser.add_argument('-d', '--destination-directory', action='store',
                  help='destination directory for generated files',required=True)

args = parser.parse_args()

options = vars(args)

db = NodeDB()
db.import_batman(list(fileinput.input(options['batmanjson'])))

if options['aliases']:
  for aliases in options['aliases']:
    db.import_aliases(json.load(open(aliases)))

if options['gateway']:
  db.mark_gateways(options['gateway'])

scriptdir = os.path.dirname(os.path.realpath(__file__))

rrd = rrd(scriptdir +  "/nodedb/",options['destination_directory'] + "/nodes")
rrd.update_database(db)
rrd.update_images()

m = D3MapBuilder(db)

nodes_json = open(options['destination_directory'] + '/nodes.json.new','w')
nodes_json.write(m.build())
nodes_json.close()
