#!/usr/bin/env python3
import time
import os

from lib.GlobalRRD import GlobalRRD
from lib.NodeRRD import NodeRRD


class RRD(object):
    def __init__(self,
                 database_directory,
                 image_path,
                 display_time_global="7d",
                 display_time_node="1d"):

        self.dbPath = database_directory
        self.globalDb = GlobalRRD(self.dbPath)
        self.imagePath = image_path
        self.displayTimeGlobal = display_time_global
        self.displayTimeNode = display_time_node

        self.currentTimeInt = (int(time.time()) / 60) * 60
        self.currentTime = str(self.currentTimeInt)

        try:
            os.stat(self.imagePath)
        except OSError:
            os.mkdir(self.imagePath)

    def update_database(self, nodes):
        node_count = 0
        client_count = 0
        for node in nodes:
            try:
                if node['flags']['online']:
                    node_count += 1
                    client_count += node['statistics']['clients']
                rrd = NodeRRD(os.path.join(self.dbPath, node['nodeinfo']['node_id'] + '.rrd'), node)
                rrd.update()
            except KeyError:
                pass
        self.globalDb.update(node_count, client_count)

    def update_images(self):
        self.globalDb.graph(os.path.join(self.imagePath, "globalGraph.png"),
                            self.displayTimeGlobal)

        nodedb_files = os.listdir(self.dbPath)

        for file_name in nodedb_files:
            if not os.path.isfile(os.path.join(self.dbPath, file_name)):
                continue

            node_name = os.path.basename(file_name).split('.')
            if node_name[1] == 'rrd' and not node_name[0] == "nodes":
                rrd = NodeRRD(os.path.join(self.dbPath, file_name))
                rrd.graph(self.imagePath, self.displayTimeNode)
