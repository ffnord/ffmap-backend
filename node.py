class Node():
  def __init__(self):
    self.name = ""
    self.id = ""
    self.macs = set()
    self.interfaces = dict()
    self.flags = dict({
      "online": False,
      "gateway": False,
    })
    self.gps = None
    self.firmware = None
    self.clientcount = 0
    self.lastseen = 0
    self.firstseen = 0

  def add_mac(self, mac):
    mac = mac.lower()
    if len(self.macs) == 0:
      self.id = mac

    self.macs.add(mac)

    self.interfaces[mac] = Interface()

  def __repr__(self):
    return '<Node %s>' % self.macs.__repr__()

class Interface():
  def __init__(self):
    self.vpn = False

