import json

__all__ = ["Exporter"]

class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that uses an object's __json__() method to convert it to
    something JSON-compatible.
    """
    def default(self, obj):
        try:
            return obj.__json__()
        except AttributeError:
            pass
        return super().default(obj)

class Exporter:
    def __init__(self, filepath="nodes.json"):
        self.filepath = filepath

    @staticmethod
    def generate(nodedb):
        indexes = {}
        nodes = []
        count = 0
        for node in set(nodedb.values()):
            nodes.append(node.export())
            indexes[node.id] = count
            count += 1

        links = []
        for node in set(nodedb.values()):
            if "neighbors" in node:
                links.extend(
                    {
                        "source": indexes[node.id],
                        "target": indexes[neighbor["neighbor"].id],
                        "quality": neighbor["metric"],
                        "type": "vpn" if neighbor["neighbor"]["vpn"] else None,
                        "id": "-".join((node.id, neighbor["neighbor"].id)),
                    } for neighbor in node["neighbors"]
                )
            if "clients" in node:
                for client in node["clients"]:
                    if not client in indexes:
                        nodes.append({
                            "id": client,
                        })
                        indexes[client] = count
                        count += 1

                    links.append({
                        "source": indexes[node.id],
                        "target": indexes[client],
                        "quality": "TT",
                        "type": "client",
                        "id": "-".join((node.id, client)),
                    })

        return {
            "nodes": nodes,
            "links": links,
        }

    def export(self, nodedb):
        with open(self.filepath, "w") as nodes_json:
            json.dump(
                self.generate(nodedb),
                nodes_json,
                cls=CustomJSONEncoder
            )
