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
      if node.flags['client']:
        continue

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
          if 'legacy' in x:
            node.flags['legacy'] = True
          self._nodes.append(node)

        node.add_mac(x['of'])
        node.add_mac(x['secondary'])

    for x in vis_data:

      if 'router' in x:
        try:
          node = self.maybe_node_by_mac((x['router'], ))
        except:
          node = Node()
          node.lastseen = self.time
          node.flags['online'] = True
          if 'legacy' in x:
            node.flags['legacy'] = True
          node.add_mac(x['router'])
          self._nodes.append(node)

        if 'gateway' in x and x['label'] == "TT":
          if x['router'] in node.macs:
            node.add_mac(x['gateway'])

            # skip processing as regular link
            continue

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
          if x['label'] == 'TT':
            node.flags['client'] = True

          node.add_mac(x['neighbor'])
          self._nodes.append(node)

    for x in vis_data:

      if 'router' in x:
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

        if x['label'] == "TT":
          link.type = "client"

        self._links.append(link)

    for x in vis_data:

      if 'primary' in x:
        try:
          node = self.maybe_node_by_mac((x['primary'], ))
        except:
          continue

        node.id = x['primary']

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
        try:
          node = self.maybe_node_mac(mac)
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
        if link.type == "client":
          continue

        source_interface = self._nodes[link.source.id].interfaces[link.source.interface]
        target_interface = self._nodes[link.target.id].interfaces[link.target.interface]
        if source_interface.vpn or target_interface.vpn:
          source_interface.vpn = True
          target_interface.vpn = True
          if link.type != "vpn":
            changes += 1

          link.type = "vpn"

  def count_clients(self):
    for link in self._links:
      try:
        a = self.maybe_node_by_id(link.source.interface)
        b = self.maybe_node_by_id(link.target.interface)

        if a.flags['client']:
          client = a
          node = b
        elif b.flags['client']:
          client = b
          node = a
        else:
          continue

        node.clientcount += 1
      except:
        pass

  def obscure_clients(self):

    globalIdCounter = 0
    nodeCounters = {}
    clientIds = {}

    for node in self._nodes:
      if node.flags['client']:
        node.macs = set()
        clientIds[node.id] = None

    for link in self._links:
      ids = link.source.interface
      idt = link.target.interface

      try:
        node_source = self.maybe_node_by_mac(ids)
        node_target = self.maybe_node_by_mac(idt)

        if not node_source.flags['client'] and not node_target.flags['client']:
          # if none of the nodes associated with this link are clients,
          # we do not want to obscure
          continue

        if ids in clientIds and idt in clientIds:
          # This is for corner cases, when a client
          # is linked to another client.
          clientIds[ids] = str(globalIdCounter)
          ids = str(globalIdCounter)
          globalIdCounter += 1

          clientIds[idt] = str(globalIdCounter)
          idt = str(globalIdCounter)
          globalIdCounter += 1

        elif ids in clientIds:
          newId = generateId(idt)
          clientIds[ids] = newId
          ids = newId

          link.source.interface = ids;
          node_source.id = ids;

        elif idt in clientIds:
          newId = generateId(ids,nodeCounters)
          clientIds[idt] = newId
          idt = newId

          link.target.interface = idt;
          node_target.id = idt;

        link.id = ids + "-" + idt

      except KeyError:
        pass

# extends node id by incremented node counter
def generateId(nodeId,nodeCounters):
  if nodeId in nodeCounters:
    n = nodeCounters[nodeId]
    nodeCounters[nodeId] = n + 1
  else:
    nodeCounters[nodeId] = 1
    n = 0

  return nodeId + "_" + str(n)
