from collections import Counter, defaultdict
from datetime import datetime
from functools import reduce

def build_mac_table(nodes):
  macs = dict()
  for node_id, node in nodes.items():
    try:
      for mac in node['nodeinfo']['network']['mesh_interfaces']:
        macs[mac] = node_id
    except KeyError:
      pass

  return macs

def prune_nodes(nodes, now, days):
  prune = []
  for node_id, node in nodes.items():
    if not 'lastseen' in node:
      prune.append(node_id)
      continue

    lastseen = datetime.strptime(node['lastseen'], '%Y-%m-%dT%H:%M:%S')
    delta = (now - lastseen).seconds

    if delta >= days * 86400:
      prune.append(node_id)

  for node_id in prune:
    del nodes[node_id]

def mark_online(node, now):
  node['lastseen'] = now.isoformat()
  node.setdefault('firstseen', now.isoformat())
  node['flags']['online'] = True

def import_nodeinfo(nodes, nodeinfos, now, assume_online=False):
  for nodeinfo in filter(lambda d: 'node_id' in d, nodeinfos):
    node = nodes.setdefault(nodeinfo['node_id'], {'flags': dict()})
    node['nodeinfo'] = nodeinfo
    node['flags']['online'] = False
    node['flags']['gateway'] = False

    if assume_online:
      mark_online(node, now)

def reset_statistics(nodes):
  for node in nodes.values():
    node['statistics'] = { 'clients': 0 }

def import_statistics(nodes, statistics):
  def add(node, statistics, target, source, f=lambda d: d):
    try:
      node['statistics'][target] = f(reduce(dict.__getitem__, source, statistics))
    except (KeyError,TypeError):
      pass

  macs = build_mac_table(nodes)
  statistics = filter(lambda d: 'node_id' in d, statistics)
  statistics = filter(lambda d: d['node_id'] in nodes, statistics)
  for node, statistics in map(lambda d: (nodes[d['node_id']], d), statistics):
    add(node, statistics, 'clients', ['clients', 'total'])
    add(node, statistics, 'gateway', ['gateway'], lambda d: macs.get(d, d))
    add(node, statistics, 'uptime', ['uptime'])
    add(node, statistics, 'loadavg', ['loadavg'])
    add(node, statistics, 'memory_usage', ['memory'], lambda d: 1 - d['free'] / d['total'])
    add(node, statistics, 'rootfs_usage', ['rootfs_usage'])

def import_mesh_ifs_vis_data(nodes, vis_data):
  macs = build_mac_table(nodes)

  mesh_ifs = defaultdict(lambda: set())
  for line in filter(lambda d: 'secondary' in d, vis_data):
    primary = line['of']
    mesh_ifs[primary].add(primary)
    mesh_ifs[primary].add(line['secondary'])

  def if_to_node(ifs):
    a = filter(lambda d: d in macs, ifs)
    a = map(lambda d: nodes[macs[d]], a)
    try:
      return (next(a), ifs)
    except StopIteration:
      return None

  mesh_nodes = filter(lambda d: d, map(if_to_node, mesh_ifs.values()))

  for v in mesh_nodes:
    node = v[0]

    try:
        mesh_ifs = set(node['nodeinfo']['network']['mesh_interfaces'])
    except KeyError:
        mesh_ifs = set()

    node['nodeinfo']['network']['mesh_interfaces'] = list(mesh_ifs | v[1])

def import_vis_clientcount(nodes, vis_data):
  macs = build_mac_table(nodes)
  data = filter(lambda d: d.get('label', None) == 'TT', vis_data)
  data = filter(lambda d: d['router'] in macs, data)
  data = map(lambda d: macs[d['router']], data)

  for node_id, clientcount in Counter(data).items():
    nodes[node_id]['statistics'].setdefault('clients', clientcount)

def mark_gateways(nodes, gateways):
  macs = build_mac_table(nodes)
  gateways = filter(lambda d: d in macs, gateways)

  for node in map(lambda d: nodes[macs[d]], gateways):
    node['flags']['gateway'] = True

def mark_vis_data_online(nodes, vis_data, now):
  macs = build_mac_table(nodes)

  online = set()
  for line in vis_data:
    if 'primary' in line:
      online.add(line['primary'])
    elif 'secondary' in line:
      online.add(line['secondary'])
    elif 'gateway' in line:
      # This matches clients' MACs.
      # On pre-Gluon nodes the primary MAC will be one of it.
      online.add(line['gateway'])

  for mac in filter(lambda d: d in macs, online):
    mark_online(nodes[macs[mac]], now)
