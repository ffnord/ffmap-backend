#!/usr/bin/env python3

import argparse
import json
import os
import sys
import networkx as nx
from datetime import datetime
from networkx.readwrite import json_graph

import alfred
import nodes
import graph
from batman import batman
from rrddb import rrd

parser = argparse.ArgumentParser()

parser.add_argument('-a', '--aliases',
                  help='read aliases from FILE',
                  default=[],
                  action='append',
                  metavar='FILE')

parser.add_argument('-m', '--mesh', action='append',
                  help='batman mesh interface')

parser.add_argument('-d', '--destination-directory', action='store',
                  help='destination directory for generated files',required=True)

parser.add_argument('--vpn', action='append', metavar='MAC',
                    help='assume MAC to be part of the VPN')

parser.add_argument('--prune', metavar='DAYS',
                    help='forget nodes offline for at least DAYS')

args = parser.parse_args()

options = vars(args)

if not options['mesh']:
  options['mesh'] = ['bat0']

nodes_fn = os.path.join(options['destination_directory'], 'nodes.json')
graph_fn = os.path.join(options['destination_directory'], 'graph.json')

now = datetime.utcnow().replace(microsecond=0)

try:
  nodedb = json.load(open(nodes_fn))

  # ignore if old format
  if 'links' in nodedb:
    raise
except:
  nodedb = {'nodes': dict()}

nodedb['timestamp'] = now.isoformat()

for node_id, node in nodedb['nodes'].items():
  node['flags']['online'] = False

nodes.import_nodeinfo(nodedb['nodes'], alfred.nodeinfo(), now, assume_online=True)

for aliases in options['aliases']:
  with open(aliases, 'r') as f:
    nodes.import_nodeinfo(nodedb['nodes'], json.load(f), now, assume_online=False)

nodes.reset_statistics(nodedb['nodes'])
nodes.import_statistics(nodedb['nodes'], alfred.statistics())

bm = list(map(lambda d: (d.vis_data(True), d.gateway_list()), map(batman, options['mesh'])))
for vis_data, gateway_list in bm:
  nodes.import_mesh_ifs_vis_data(nodedb['nodes'], vis_data)
  nodes.import_vis_clientcount(nodedb['nodes'], vis_data)
  nodes.mark_vis_data_online(nodedb['nodes'], vis_data, now)
  nodes.mark_gateways(nodedb['nodes'], gateway_list)

if options['prune']:
  nodes.prune_nodes(nodedb['nodes'], now, int(options['prune']))

batadv_graph = nx.DiGraph()
for vis_data, gateway_list in bm:
  graph.import_vis_data(batadv_graph, nodedb['nodes'], vis_data)

if options['vpn']:
  graph.mark_vpn(batadv_graph, frozenset(options['vpn']))

batadv_graph = graph.merge_nodes(batadv_graph)
batadv_graph = graph.to_undirected(batadv_graph)

with open(nodes_fn, 'w') as f:
  json.dump(nodedb, f)

with open(graph_fn, 'w') as f:
  json.dump({'batadv': json_graph.node_link_data(batadv_graph)}, f)

scriptdir = os.path.dirname(os.path.realpath(__file__))
rrd = rrd(scriptdir +  '/nodedb/', options['destination_directory'] + '/nodes')
rrd.update_database(nodedb['nodes'])
rrd.update_images()
