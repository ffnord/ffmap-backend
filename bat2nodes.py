#!/usr/bin/env python3

import json
import fileinput
import argparse
import os
import time

from batman import batman
from alfred import alfred
from rrddb import rrd
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

parser.add_argument('-m', '--mesh', action='append',
                  default=["bat0"],
                  help='batman mesh interface')

parser.add_argument('-A', '--alfred', action='store_true',
                  help='retrieve aliases from alfred')

parser.add_argument('-d', '--destination-directory', action='store',
                  help='destination directory for generated files',required=True)

args = parser.parse_args()

options = vars(args)

db = NodeDB(int(time.time()))

for mesh_interface in options['mesh']:
  bm = batman(mesh_interface)
  db.parse_vis_data(bm.vis_data(options['alfred']))
  for gw in bm.gateway_list():
    db.mark_gateway(gw)

if options['aliases']:
  for aliases in options['aliases']:
    db.import_aliases(json.load(open(aliases)))

if options['alfred']:
  af = alfred()
  db.import_aliases(af.aliases())

db.load_state("state.json")

# remove nodes that have been offline for more than 30 days
db.prune_offline(time.time() - 30*86400)

db.dump_state("state.json")

scriptdir = os.path.dirname(os.path.realpath(__file__))

m = D3MapBuilder(db)

#Write nodes json
nodes_json = open(options['destination_directory'] + '/nodes.json.new','w')
nodes_json.write(m.build())
nodes_json.close()

#Move to destination
os.rename(options['destination_directory'] + '/nodes.json.new',options['destination_directory'] + '/nodes.json')

rrd = rrd(scriptdir +  "/nodedb/", options['destination_directory'] + "/nodes")
rrd.update_database(db)
rrd.update_images()
