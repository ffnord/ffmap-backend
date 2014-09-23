#!/usr/bin/env python3
import subprocess
import time
import os
from GlobalRRD import GlobalRRD
from NodeRRD import NodeRRD

class rrd:
  def __init__( self
              , databaseDirectory
              , imagePath
              , displayTimeGlobal = "7d"
              , displayTimeNode = "1d"
              ):
    self.dbPath = databaseDirectory
    self.globalDb = GlobalRRD(self.dbPath)
    self.imagePath = imagePath
    self.displayTimeGlobal = displayTimeGlobal
    self.displayTimeNode = displayTimeNode

    self.currentTimeInt = (int(time.time())/60)*60
    self.currentTime    = str(self.currentTimeInt)

    try:
      os.stat(self.imagePath)
    except:
      os.mkdir(self.imagePath)

  def update_database(self, nodes):
    online_nodes = dict(filter(lambda d: d[1]['flags']['online'], nodes.items()))
    client_count = sum(map(lambda d: d['statistics']['clients'], online_nodes.values()))

    self.globalDb.update(len(online_nodes), client_count)
    for node_id, node in online_nodes.items():
      rrd = NodeRRD(os.path.join(self.dbPath, node_id + '.rrd'), node)
      rrd.update()

  def update_images(self):
    self.globalDb.graph(os.path.join(self.imagePath, "globalGraph.png"), self.displayTimeGlobal)

    nodeDbFiles = os.listdir(self.dbPath)

    for fileName in nodeDbFiles:
      if not os.path.isfile(os.path.join(self.dbPath, fileName)):
        continue

      nodeName = os.path.basename(fileName).split('.')
      if nodeName[1] == 'rrd' and not nodeName[0] == "nodes":
        rrd = NodeRRD(os.path.join(self.dbPath, fileName))
        rrd.graph(self.imagePath, self.displayTimeNode)
