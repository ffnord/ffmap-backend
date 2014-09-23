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

  def update_database(self,db):
    nodes = db.get_nodes()
    clientCount = sum(map(lambda d: d.clientcount, nodes))

    curtime = time.time() - 60
    self.globalDb.update(len(list(filter(lambda x: x.lastseen >= curtime, nodes))), clientCount)
    for node in nodes:
      rrd = NodeRRD(
        os.path.join(self.dbPath, str(node.id).replace(':', '') + '.rrd'),
        node
      )
      rrd.update()

  def update_images(self):
    """ Creates an image for every rrd file in the database directory.
    """

    self.globalDb.graph(os.path.join(self.imagePath, "globalGraph.png"), self.displayTimeGlobal)

    nodeDbFiles = os.listdir(self.dbPath)

    for fileName in nodeDbFiles:
      if not os.path.isfile(os.path.join(self.dbPath, fileName)):
        continue

      nodeName = os.path.basename(fileName).split('.')
      if nodeName[1] == 'rrd' and not nodeName[0] == "nodes":
        rrd = NodeRRD(os.path.join(self.dbPath, fileName))
        rrd.graph(self.imagePath, self.displayTimeNode)
