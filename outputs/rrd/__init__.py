import os
from .NodeRRD import NodeRRD
from .GlobalRRD import GlobalRRD

class Exporter:
    def __init__(self, directory="nodedb"):
        self.directory = directory
        try:
            os.mkdir(self.directory)
        except OSError:
            pass

    def export(self, nodedb):
        nodes = set(nodedb.values())
        clients = 0
        nodecount = 0
        for node in nodes:
            clients += len(node.get("clients", []))
            nodecount += 1
            NodeRRD(
                os.path.join(
                    self.directory,
                    str(node.id).replace(':', '') + '.rrd'
                ),
                node
            ).update()

        GlobalRRD(os.path.join(self.directory, "nodes.rrd")).update(
            nodecount,
            clients
        )
