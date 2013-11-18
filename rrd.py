#!/usr/bin/env python3
import subprocess
import time
import os

class rrd:
  def __init__( self
              , databaseDirectory
              , imagePath
              , displayTimeGlobal = "7d"
              , displayTimeNode = "1d"
              ):
    self.dbPath = databaseDirectory
    self.globalDbFile = databaseDirectory + "/nodes.rrd"
    self.imagePath = imagePath
    self.displayTimeGlobal = displayTimeGlobal
    self.displayTimeNode = displayTimeNode
    
    self.currentTimeInt = (int(time.time())/60)*60
    self.currentTime    = str(self.currentTimeInt)

  def checkAndCreateIfNeededGlobalDatabase(self):
    """ Creates the global database file iff it did not exist.
    """
    if not os.path.exists(self.globalDbFile):
      # Create Database with rrdtool
      args =  ["rrdtool",'create', self.globalDbFile
              ,'--start', str(round(self.currentTimeInt - 60))
              ,'--step' , '60'
              # Number of nodes available
              ,'DS:nodes:GAUGE:120:0:U'
              ,'RRA:LAST:0:1:44640'
              ,'RRA:LAST:0:60:744'
              ,'RRA:LAST:0:1440:1780'
              # Number of client available
              ,'DS:clients:GAUGE:120:0:U'
              ,'RRA:LAST:0:1:44640'
              ,'RRA:LAST:0:60:744'
              ,'RRA:LAST:0:1440:1780'
              ]
      subprocess.call(args)

  def updateGlobalDatabase(self,nodeCount,clientCount):
    """ Adds a new (#Nodes,#Clients) entry to the global database.
    """
    # Update Global RRDatabase
    args =  ["rrdtool",'updatev', self.globalDbFile
            # #Nodes #Clients
            , self.currentTime + ":"+str(nodeCount)+":"+str(clientCount)
            ]
    subprocess.check_output(args)

  def createGlobalGraph(self):
    nodeGraph = self.imagePath + "/" + "globalGraph.png"
    args = ["rrdtool", 'graph', nodeGraph, '-s', '-' + self.displayTimeGlobal, '-w', '800', '-h' '400'
           ,'DEF:nodes=' + self.globalDbFile + ':nodes:LAST', 'LINE1:nodes#F00:nodes\\l'
           ,'DEF:clients=' + self.globalDbFile + ':clients:LAST','LINE2:clients#00F:clients'
           ]
    subprocess.check_output(args)


  def nodeMACToRRDFile(self,nodeMAC):
    return self.dbPath + "/" + str(nodeMAC).replace(":","") + ".rrd"

  def nodeMACToPNGFile(self,nodeMAC):
    return self.imagePath + "/" + str(nodeMAC).replace(":","") + ".png"

  def checkAndCreateIfNeededNodeDatabase(self,nodePrimaryMAC):
    # TODO check for bad nodeNames
    nodeFile = self.nodeMACToRRDFile(nodePrimaryMAC);
    if not os.path.exists(nodeFile):
      # TODO Skalen anpassen
      args = ["rrdtool",'create',nodeFile
             ,'--start',str(round(self.currentTimeInt - 60))
             ,'--step' , '60'
             ,'DS:upstate:GAUGE:120:0:1'
             ,'RRA:LAST:0:1:44640'
             # Number of client available
             ,'DS:clients:GAUGE:120:0:U'
             ,'RRA:LAST:0:1:44640'
             ]
      subprocess.check_output(args)

  # Call only if node is up
  def updateNodeDatabase(self,nodePrimaryMAC,clientCount):
    nodeFile = self.nodeMACToRRDFile(nodePrimaryMAC)
    # Update Global RRDatabase
    args =  ["rrdtool",'updatev', nodeFile
            # #Upstate #Clients
            , self.currentTime + ":"+str(1)+":"+str(clientCount)
            ]
    subprocess.check_output(args)

  def createNodeGraph(self,nodePrimaryMAC,displayTimeNode):
    nodeGraph = self.nodeMACToPNGFile(nodePrimaryMAC)
    nodeFile  = self.nodeMACToRRDFile(nodePrimaryMAC)
    args = ['rrdtool','graph', nodeGraph, '-s', '-' + self.displayTimeNode , '-w', '800', '-h', '400', '-l', '0', '-y', '1:1',
            'DEF:clients=' + nodeFile + ':clients:LAST',
            'VDEF:maxc=clients,MAXIMUM',
            'CDEF:c=0,clients,ADDNAN',
            'CDEF:d=clients,UN,maxc,UN,1,maxc,IF,*',
            'AREA:c#0F0:up\\l',
            'AREA:d#F00:down\\l',
            'LINE1:c#00F:clients connected\\l',
            ]
    subprocess.check_output(args)

  def update_database(self,db):
    nodes = {}
    clientCount = 0
    for node in db.get_nodes():
      if node.flags['online']:
        if not node.flags['client']:
          nodes[node.id] = node
          node.clients = 0;
        else:
          clientCount += 1
    for link in db.get_links():
      source = link.source.interface
      target = link.target.interface
      if source in nodes and not target in nodes:
        nodes[source].clients += 1
      elif target in nodes and not source in nodes:
        nodes[target].clients += 1

    self.checkAndCreateIfNeededGlobalDatabase()
    self.updateGlobalDatabase(len(nodes),clientCount)
    for mac in nodes:
      self.checkAndCreateIfNeededNodeDatabase(mac)
      self.updateNodeDatabase(mac,nodes[mac].clients)

  def update_images(self):
    """ Creates a image for every rrd file in the database directory.
    """

    self.createGlobalGraph()

    nodeDbFiles = os.listdir(self.dbPath)

    for fileName in nodeDbFiles:
      nodeName = os.path.basename(fileName).split('.')
      if nodeName[1] == 'rrd' and not nodeName[0] == "nodes":
        self.createNodeGraph(nodeName[0],self.displayTimeNode)
