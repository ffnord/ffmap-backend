class Link():
  def __init__(self):
    self.id = None
    self.source = LinkConnector()
    self.target = LinkConnector()
    self.quality = None
    self.type = None

  def export(self):
    return {
      'source': self.source.id,
      'target': self.target.id,
      'quality': self.quality,
      'type': self.type,
      'id': self.id
    }

class LinkConnector():
  def __init__(self):
    self.id = None
    self.interface = None

  def __repr__(self):
    return "LinkConnector(%d, %s)" % (self.id, self.interface)
