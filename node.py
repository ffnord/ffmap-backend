from collections import defaultdict

class NoneDict:
  """
  A NoneDict acts like None but returns a NoneDict for every item in it.

  This is similar to the behaviour of collections.defaultdict in that even
  previously inexistent keys can be accessed, but there is nothing stored
  permanently.
  """
  __repr__ = lambda self: 'NoneDict()'
  __bool__ = lambda self: False
  __getitem__ = lambda self, k: NoneDict()
  __json__ = lambda self: None
  def __setitem__(self, key, value):
    raise RuntimeError("NoneDict is readonly")

class casualdict(defaultdict):
  """
  This special defaultdict returns a NoneDict for inexistent items. Also, its
  items can be accessed as attributed as well.
  """
  def __init__(self):
    super().__init__(NoneDict)
  __getattr__ = defaultdict.__getitem__
  __setattr__ = defaultdict.__setitem__

class Node(casualdict):
  def __init__(self):
    self.name = ""
    self.id = ""
    self.macs = set()
    self.interfaces = dict()
    self.flags = dict({
      "online": False,
      "gateway": False,
      "client": False
    })
    super().__init__()

  def add_mac(self, mac):
    mac = mac.lower()
    if len(self.macs) == 0:
      self.id = mac

    self.macs.add(mac)

    self.interfaces[mac] = Interface()

  def __repr__(self):
    return self.macs.__repr__()

  def export(self):
    """
    Return a dict that contains all attributes of the Node that are supposed to
    be exported to other applications.
    """
    return {
      "name": self.name,
      "id": self.id,
      "macs": list(self.macs),
      "geo": self.geo,
      "firmware": self.software['firmware']['release'],
      "flags": self.flags
    }

class Interface():
  def __init__(self):
    self.vpn = False
