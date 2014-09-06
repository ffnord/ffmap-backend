import json
from datetime import datetime

__all__ = ["Exporter"]

class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that uses an object's __json__() method to convert it
    to something JSON-compatible.
    """
    def default(self, obj):
        try:
            return obj.__json__()
        except AttributeError:
            pass
        return super().default(obj)

class Output:
    def __init__(self, filepath="nodes.json"):
        self.filepath = filepath

    @staticmethod
    def generate(nodedb):
        indexes = {}
        nodes = []
        count = 0
        for node in set(nodedb.values()):
            node_export = node.export()
            node_export["flags"] = {
                "gateway": "vpn" in node and node["vpn"],
                "client": False,
                "online": True
            }
            nodes.append(node_export)
            indexes[node.id] = count
            count += 1

        links = {}
        for node in set(nodedb.values()):
            for neighbor in node.get("neighbors", []):
                key = (neighbor["neighbor"].id, node.id)
                rkey = tuple(reversed(key))
                if rkey in links:
                    links[rkey]["quality"] += ","+neighbor["metric"]
                else:
                    links[key] = {
                        "source": indexes[node.id],
                        "target": indexes[neighbor["neighbor"].id],
                        "quality": neighbor["metric"],
                        "type": "vpn" if neighbor["neighbor"]["vpn"] or node["vpn"] else None,
                        "id": "-".join((node.id, neighbor["neighbor"].id)),
                    }
            clientcount = 0
            for client in node.get("clients", []):
                nodes.append({
                    "id": "%s-%s" % (node.id, clientcount),
                    "flags": {
                        "client": True,
                        "online": True,
                        "gateway": False
                    }
                })
                indexes[client] = count

                links[(node.id, client)] = {
                    "source": indexes[node.id],
                    "target": indexes[client],
                    "quality": "TT",
                    "type": "client",
                    "id": "%s-%i" % (node.id, clientcount),
                }
                count += 1
                clientcount += 1

        return {
            "nodes": nodes,
            "links": list(links.values()),
            "meta": {
                "timestamp": datetime.utcnow()
                                     .replace(microsecond=0)
                                     .isoformat()
            }
        }

    def output(self, nodedb):
        with open(self.filepath, "w") as nodes_json:
            json.dump(
                self.generate(nodedb),
                nodes_json,
                cls=CustomJSONEncoder
            )
