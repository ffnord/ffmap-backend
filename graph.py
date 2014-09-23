import networkx as nx
from copy import deepcopy
from functools import reduce
from itertools import chain
from nodes import build_mac_table

def import_vis_data(graph, nodes, vis_data):
  macs = build_mac_table(nodes)
  nodes_a = map(lambda d: 2*[d['primary']], filter(lambda d: 'primary' in d, vis_data))
  nodes_b = map(lambda d: [d['secondary'], d['of']], filter(lambda d: 'secondary' in d, vis_data))
  graph.add_nodes_from(map(lambda a, b: (a, dict(primary=b, node_id=macs.get(b))), *zip(*chain(nodes_a, nodes_b))))

  edges = filter(lambda d: 'neighbor' in d, vis_data)
  graph.add_edges_from(map(lambda d: (d['router'], d['neighbor'], dict(tq=float(d['label']))), edges))

def mark_vpn(graph, vpn_macs):
  components = map(frozenset, nx.weakly_connected_components(graph))
  components = filter(vpn_macs.intersection, components)
  nodes = reduce(lambda a, b: a | b, components, set())

  for node in nodes:
    for k, v in graph[node].items():
      v['vpn'] = True

def to_multigraph(graph):
  def f(a):
    node = graph.node[a]
    return node['primary'] if node else a

  G = nx.MultiDiGraph()
  map_node = lambda node, data: (data['primary'], dict(node_id=data['node_id'])) if data else (node, dict())
  G.add_nodes_from(map(map_node, *zip(*graph.nodes_iter(data=True))))
  G.add_edges_from(map(lambda a, b, data: (f(a), f(b), data), *zip(*graph.edges_iter(data=True))))

  return G

def merge_nodes(graph):
  def merge_edges(data):
    tq = min(map(lambda d: d['tq'], data))
    vpn = all(map(lambda d: d.get('vpn', False), data))
    return dict(tq=tq, vpn=vpn)

  G = to_multigraph(graph)
  H = nx.DiGraph()
  H.add_nodes_from(G.nodes_iter(data=True))
  edges = chain.from_iterable([[(e, d, merge_edges(G[e][d].values())) for d in G[e]] for e in G])
  H.add_edges_from(edges)

  return H

def to_undirected(graph):
  G = nx.MultiGraph()
  G.add_nodes_from(graph.nodes_iter(data=True))
  G.add_edges_from(graph.edges_iter(data=True))

  def merge_edges(data):
    tq = max(map(lambda d: d['tq'], data))
    vpn = all(map(lambda d: d.get('vpn', False), data))
    return dict(tq=tq, vpn=vpn, bidirect=len(data) == 2)

  H = nx.Graph()
  H.add_nodes_from(G.nodes_iter(data=True))
  edges = chain.from_iterable([[(e, d, merge_edges(G[e][d].values())) for d in G[e]] for e in G])
  H.add_edges_from(edges)

  return H
