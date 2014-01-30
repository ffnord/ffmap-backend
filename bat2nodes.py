#!/usr/bin/env python3

import json
import fileinput
import argparse
import os

from batman import batman
from alfred import alfred
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

parser.add_argument('-m', '--mesh', action='append',
                  help='batman mesh interface')

parser.add_argument('-o', '--obscure', action='store_true',
                  help='obscure client macs')

parser.add_argument('-A', '--alfred', action='store_true',
                  help='retrieve aliases from alfred')

parser.add_argument('-d', '--destination-directory', action='store',
                  help='destination directory for generated files',required=True)

args = parser.parse_args()

options = vars(args)

db = NodeDB()
if options['mesh']:
  for mesh_interface in options['mesh']:
    bm = batman(mesh_interface)
    db.parse_vis_data(bm.vis_data(options['alfred']))
    for gw in bm.gateway_list():
      db.mark_gateways(gw.mac)
else:
  bm = batman()
  db.parse_vis_data(bm.vis_data(options['alfred']))
  for gw in bm.gateway_list():
    db.mark_gateways([gw['mac']])

if options['aliases']:
  for aliases in options['aliases']:
    db.import_aliases(json.load(open(aliases)))

if options['alfred']:
  af = alfred()
  db.import_aliases(af.aliases())

if options['obscure']:
  db.obscure_clients()

scriptdir = os.path.dirname(os.path.realpath(__file__))

rrd = rrd(scriptdir +  "/nodedb/", options['destination_directory'] + "/nodes")
rrd.update_database(db)
rrd.update_images()

m = D3MapBuilder(db)

#Write nodes json
nodes_json = open(options['destination_directory'] + '/nodes.json.new','w')
nodes_json.write(m.build())
nodes_json.close()

#Move to destination
os.rename(options['destination_directory'] + '/nodes.json.new',options['destination_directory'] + '/nodes.json')
