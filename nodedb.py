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
          except:
            node = Node()
            node.id = n['id']
            node.name = n['name']
            node.lastseen = n['lastseen']
            node.gps = n['geo']
            self._nodes.append(node)

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
        except:
          node = Node()
          node.lastseen = self.time
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
        except:
          node = Node()
          node.lastseen = self.time
          node.flags['online'] = True
          node.add_mac(x['router'])
          self._nodes.append(node)

        try:
          if 'neighbor' in x:
            try:
              node = self.maybe_node_by_mac((x['neighbor']))
            except:
              continue

          if 'gateway' in x:
            x['neighbor'] = x['gateway']

          node = self.maybe_node_by_mac((x['neighbor'], ))
        except:
          node = Node()
          node.lastseen = self.time
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
        except:
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
        except:
          continue

        node.id = x['primary']

    for x in vis_data:
      if 'router' in x and x['label'] == 'TT':
        try:
          node = self.maybe_node_by_mac((x['router'], ))
          node.add_mac(x['gateway'])
          if not is_similar(x['router'], x['gateway']):
            node.clientcount += 1
        except:
          pass

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
      except:
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

  # list of macs
  # if options['gateway']:
  #   mark_gateways(options['gateway'])
  def mark_gateways(self, gateways):
    for gateway in gateways:
      try:
        node = self.maybe_node_by_mac((gateway, ))
      except:
        print("WARNING: did not find gateway '",gateway,"' in node list")
        continue

      node.flags['gateway'] = True

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

# compares two MACs and decides whether they are
# similar and could be from the same node
def is_similar(a, b):
  if a == b:
    return True

  try:
    mac_a = list(int(i, 16) for i in a.split(":"))
    mac_b = list(int(i, 16) for i in b.split(":"))
  except ValueError:
    return False

  # first byte must only differ in bit 2
  if mac_a[0] | 2 == mac_b[0] | 2:
    # count different bytes
    c = [x for x in zip(mac_a[1:], mac_b[1:]) if x[0] != x[1]]
  else:
    return False

  # no more than two additional bytes must differ
  if len(c) <= 2:
    delta = 0

  if len(c) > 0:
    delta = sum(abs(i[0] -i[1]) for i in c)

  # These addresses look pretty similar!
  return delta < 8

def is_derived_mac(a, b):
  if a == b:
    return True

  try:
    mac_a = list(int(i, 16) for i in a.split(":"))
    mac_b = list(int(i, 16) for i in b.split(":"))
  except ValueError:
    return False

  if mac_a[4] != mac_b[4] or mac_a[2] != mac_b[2] or mac_a[1] != mac_b[1]:
    return False

  x = list(mac_a)
  x[5] += 1
  x[5] %= 255
  if mac_b == x:
    return True

  x[0] |= 2
  if mac_b == x:
    return True

  x[3] += 1
  x[3] %= 255
  if mac_b == x:
    return True

  x = list(mac_a)
  x[0] |= 2
  x[5] += 2
  x[5] %= 255
  if mac_b == x:
    return True

  x = list(mac_a)
  x[0] |= 2
  x[3] += 1
  x[3] %= 255
  if mac_b == x:
    return True

  return False
