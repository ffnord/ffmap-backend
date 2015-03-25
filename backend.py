#!/usr/bin/env python3
"""
backend.py - ffmap-backend runner
https://github.com/ffnord/ffmap-backend
"""
import argparse
import json
import os
from datetime import datetime

import networkx as nx
from networkx.readwrite import json_graph

from lib import graph, nodes
from lib.alfred import Alfred
from lib.batman import Batman
from lib.rrddb import RRD


def main(params):
    nodes_fn = os.path.join(params['dest_dir'], 'nodes.json')
    graph_fn = os.path.join(params['dest_dir'], 'graph.json')

    now = datetime.utcnow().replace(microsecond=0)

    # read nodedb state from node.json
    with open(nodes_fn, 'r') as nodedb_handle:
        nodedb = json.load(nodedb_handle)
    # flush nodedb if it uses the old format
    if 'links' in nodedb:
        nodedb = {'nodes': dict()}

    # update timestamp and assume all nodes are offline
    nodedb['timestamp'] = now.isoformat()
    for node_id, node in nodedb['nodes'].items():
        node['flags']['online'] = False

    # integrate alfred nodeinfo
    alfred = Alfred(unix_sockpath=params['alfred_sock'])
    nodes.import_nodeinfo(nodedb['nodes'], alfred.nodeinfo(),
                          now, assume_online=True)

    # integrate static aliases data
    for aliases in params['aliases']:
        with open(aliases, 'r') as f:
            nodes.import_nodeinfo(nodedb['nodes'], json.load(f),
                                  now, assume_online=False)

    nodes.reset_statistics(nodedb['nodes'])
    nodes.import_statistics(nodedb['nodes'], alfred.statistics())

    # initialize batman bindings for each mesh interface
    # and acquire gwl and visdata
    mesh_interfaces = frozenset(params['mesh'])
    mesh_info = {}
    for interface in mesh_interfaces:
        bm = Batman(mesh_interface=interface,
                    alfred_sockpath=params['alfred_sock'])
        vd = bm.vis_data(True)
        gwl = bm.gateway_list()

        mesh_info[interface] = (vd, gwl)

    # update nodedb from batman-adv data
    for vd, gwl in mesh_info.values():
        nodes.import_mesh_ifs_vis_data(nodedb['nodes'], vd)
        nodes.import_vis_clientcount(nodedb['nodes'], vd)
        nodes.mark_vis_data_online(nodedb['nodes'], vd, now)
        nodes.mark_gateways(nodedb['nodes'], gwl)

    # clear the nodedb from nodes that have not been online in $prune days
    if params['prune']:
        nodes.prune_nodes(nodedb['nodes'], now, int(params['prune']))

    # build nxnetworks graph from nodedb and visdata
    batadv_graph = nx.DiGraph()
    for vd, gwl in mesh_info.values():
        graph.import_vis_data(batadv_graph, nodedb['nodes'], vd)

    # force mac addresses to be vpn-link only (like gateways for example)
    if params['vpn']:
        graph.mark_vpn(batadv_graph, frozenset(params['vpn']))

    batadv_graph = graph.merge_nodes(batadv_graph)
    batadv_graph = graph.to_undirected(batadv_graph)

    # write processed data to dest dir
    with open(nodes_fn, 'w') as f:
        json.dump(nodedb, f)

    with open(graph_fn, 'w') as f:
        json.dump({'batadv': json_graph.node_link_data(batadv_graph)}, f)

    # optional rrd graphs (trigger with --rrd)
    if params['rrd']:
        script_directory = os.path.dirname(os.path.realpath(__file__))
        rrd = RRD(os.path.join(script_directory, 'nodedb'),
                  os.path.join(params['dest_dir'], 'nodes'))
        rrd.update_database(nodedb['nodes'])
        rrd.update_images()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--aliases',
                        help='read aliases from FILE',
                        default=[], action='append',
                        metavar='FILE')
    parser.add_argument('-m', '--mesh', action='append',
                        default=['bat0'],
                        help='batman mesh interface (defaults to bat0)')
    parser.add_argument('-s', '--alfred-sock',
                        default=None,
                        help='alfred unix socket path')
    parser.add_argument('-d', '--dest-dir', action='store',
                        help='destination directory for generated files',
                        required=True)
    parser.add_argument('--vpn', action='append', metavar='MAC',
                        help='assume MAC to be part of the VPN')
    parser.add_argument('--prune', metavar='DAYS',
                        help='forget nodes offline for at least DAYS')
    parser.add_argument('--rrd', dest='rrd', action='store_true',
                        default=False,
                        help='create RRD graphs')

    options = vars(parser.parse_args())

    main(options)
