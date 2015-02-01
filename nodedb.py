import json
from functools import reduce
from collections import defaultdict
from node import Node, Interface
from link import Link, LinkConnector

class NodeDB:
  def __init__(self, time=0):
    self.time = time
    self._nodes = []
    self._links = []

  # fetch list of links
  def get_links(self):
    self.update_vpn_links()
    return self.reduce_links()

  # fetch list of nodes
  def get_nodes(self):
    return self._nodes

  # remove all offlines nodes with lastseen < timestamp
  def prune_offline(self, timestamp):
    self._nodes = list(filter(lambda x: x.lastseen >= timestamp, self._nodes))

  # write persistent state to file
  def dump_state(self, filename):
    obj = []

    for node in self._nodes:
      obj.append({ 'id': node.id
                 , 'name': node.name
                 , 'lastseen': node.lastseen
                 , 'firstseen': node.firstseen
                 , 'geo': node.gps
                 })

    with open(filename, "w") as f:
      json.dump(obj, f)

  # load persistent state from file
  def load_state(self, filename):
    try:
      with open(filename, "r") as f:
        obj = json.load(f)
        for n in obj:
          try:
            node = self.maybe_node_by_id(n['id'])
          except KeyError:
            node = Node()
            node.id = n['id']
            node.name = n['name']
            node.lastseen = n['lastseen']
            node.gps = n['geo']
            self._nodes.append(node)

          if 'firstseen' in n:
            node.firstseen = n['firstseen']

    except:
      pass

  def maybe_node_by_mac(self, macs):
    for node in self._nodes:
      for mac in macs:
        if mac.lower() in node.macs:
          return node

    raise KeyError

  def maybe_node_by_id(self, mac):
    for node in self._nodes:
      if mac.lower() == node.id:
        return node

    raise KeyError

  def parse_vis_data(self,vis_data):
    for x in vis_data:

      if 'of' in x:
        try:
          node = self.maybe_node_by_mac((x['of'], x['secondary']))
        except KeyError:
          node = Node()
          node.lastseen = self.time
          node.firstseen = self.time
          node.flags['online'] = True
          self._nodes.append(node)

        node.add_mac(x['of'])
        node.add_mac(x['secondary'])

    for x in vis_data:
      if 'router' in x:
        # TTs will be processed later
        if x['label'] == "TT":
          continue

        try:
          node = self.maybe_node_by_mac((x['router'], ))
        except KeyError:
          node = Node()
          node.lastseen = self.time
          node.firstseen = self.time
          node.flags['online'] = True
          node.add_mac(x['router'])
          self._nodes.append(node)

        try:
          if 'neighbor' in x:
            try:
              node = self.maybe_node_by_mac((x['neighbor'], ))
            except KeyError:
              continue

          if 'gateway' in x:
            x['neighbor'] = x['gateway']

          node = self.maybe_node_by_mac((x['neighbor'], ))
        except KeyError:
          node = Node()
          node.lastseen = self.time
          node.firstseen = self.time
          node.flags['online'] = True
          node.add_mac(x['neighbor'])
          self._nodes.append(node)

    for x in vis_data:
      if 'router' in x:
        # TTs will be processed later
        if x['label'] == "TT":
          continue

        try:
          if 'gateway' in x:
            x['neighbor'] = x['gateway']

          router = self.maybe_node_by_mac((x['router'], ))
          neighbor = self.maybe_node_by_mac((x['neighbor'], ))
        except KeyError:
          continue

        # filter TT links merged in previous step
        if router == neighbor:
          continue

        link = Link()
        link.source = LinkConnector()
        link.source.interface = x['router']
        link.source.id = self._nodes.index(router)
        link.target = LinkConnector()
        link.target.interface = x['neighbor']
        link.target.id = self._nodes.index(neighbor)
        link.quality = x['label']
        link.id = "-".join(sorted((link.source.interface, link.target.interface)))

        self._links.append(link)

    for x in vis_data:
      if 'primary' in x:
        try:
          node = self.maybe_node_by_mac((x['primary'], ))
        except KeyError:
          continue

        node.id = x['primary']

    for x in vis_data:
      if 'router' in x and x['label'] == 'TT':
        try:
          node = self.maybe_node_by_mac((x['router'], ))
          node.add_mac(x['gateway'])
          node.clientcount += 1
        except KeyError:
          pass
 
    # don't count node as its own client
    for node in self._nodes:
      if node.clientcount > 0:
        node.clientcount -= 1

  def reduce_links(self):
    tmp_links = defaultdict(list)

    for link in self._links:
      tmp_links[link.id].append(link)

    links = []

    def reduce_link(a, b):
      a.id = b.id
      a.source = b.source
      a.target = b.target
      a.type = b.type
      a.quality = ", ".join([x for x in (a.quality, b.quality) if x])

      return a

    for k, v in tmp_links.items():
      new_link = reduce(reduce_link, v, Link())
      links.append(new_link)

    return links

  def import_aliases(self, aliases):
    for mac, alias in aliases.items():
      try:
        node = self.maybe_node_by_mac([mac])
      except KeyError:
        # create an offline node
        node = Node()
        node.add_mac(mac)
        self._nodes.append(node)

      if 'name' in alias:
        node.name = alias['name']

      if 'vpn' in alias and alias['vpn'] and mac and node.interfaces and mac in node.interfaces:
        node.interfaces[mac].vpn = True

      if 'gps' in alias:
        node.gps = alias['gps']

      if 'firmware' in alias:
        node.firmware = alias['firmware']

      if 'id' in alias:
        node.id = alias['id']

  def mark_gateway(self, gateway):
    try:
      node = self.maybe_node_by_mac((gateway, ))
      node.flags['gateway'] = True
    except KeyError:
      print("WARNING: did not find gateway ", gateway, " in node list")

  def update_vpn_links(self):
    changes = 1
    while changes > 0:
      changes = 0
      for link in self._links:
        source_interface = self._nodes[link.source.id].interfaces[link.source.interface]
        target_interface = self._nodes[link.target.id].interfaces[link.target.interface]
        if source_interface.vpn or target_interface.vpn:
          source_interface.vpn = True
          target_interface.vpn = True
          if link.type != "vpn":
            changes += 1

          link.type = "vpn"
