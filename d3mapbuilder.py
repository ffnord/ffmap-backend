import json
import datetime

class D3MapBuilder:
  def __init__(self, db):
    self._db = db

  def build(self):
    output = dict()

    now = datetime.datetime.utcnow().replace(microsecond=0)

    nodes = self._db.get_nodes()

    output['nodes'] = [{'name': x.name, 'id': x.id,
                        'macs': ', '.join(x.macs),
                        'geo': [float(x) for x in x.gps.split(" ")] if x.gps else None,
                        'firmware': x.firmware,
                        'flags': x.flags,
                        'clientcount': x.clientcount
                       } for x in nodes]

    links = self._db.get_links()

    output['links'] = [{'source': x.source.id, 'target': x.target.id,
                        'quality': x.quality,
                        'type': x.type,
                        'id': x.id
                       } for x in links]

    output['meta'] = {
                      'timestamp': now.isoformat()
                     }

    return json.dumps(output)

