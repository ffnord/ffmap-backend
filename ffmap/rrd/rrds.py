import os
import subprocess
from ffmap.node import Node
from . import RRD, DS, RRA

class NodeRRD(RRD):
    ds_list = [
        DS('upstate', 'GAUGE', 120, 0, 1),
        DS('clients', 'GAUGE', 120, 0, float('NaN')),
        DS('neighbors', 'GAUGE', 120, 0, float('NaN')),
        DS('vpn_neighbors', 'GAUGE', 120, 0, float('NaN')),
        DS('loadavg', 'GAUGE', 120, 0, float('NaN')),
        DS('rx_bytes', 'DERIVE', 120, 0, float('NaN')),
        DS('rx_packets', 'DERIVE', 120, 0, float('NaN')),
        DS('tx_bytes', 'DERIVE', 120, 0, float('NaN')),
        DS('tx_packets', 'DERIVE', 120, 0, float('NaN')),
        DS('mgmt_rx_bytes', 'DERIVE', 120, 0, float('NaN')),
        DS('mgmt_rx_packets', 'DERIVE', 120, 0, float('NaN')),
        DS('mgmt_tx_bytes', 'DERIVE', 120, 0, float('NaN')),
        DS('mgmt_tx_packets', 'DERIVE', 120, 0, float('NaN')),
        DS('forward_bytes', 'DERIVE', 120, 0, float('NaN')),
        DS('forward_packets', 'DERIVE', 120, 0, float('NaN')),
    ]
    rra_list = [
        RRA('AVERAGE', 0.5, 1, 120),    #  2 hours of  1 minute samples
        RRA('AVERAGE', 0.5, 5, 1440),   #  5 days  of  5 minute samples
        RRA('AVERAGE', 0.5, 60, 720),   # 30 days  of  1 hour   samples
        RRA('AVERAGE', 0.5, 720, 730),  #  1 year  of 12 hour   samples
    ]

    def __init__(self, filename, node = None):
        """
        Create a new RRD for a given node.

        If the RRD isn't supposed to be updated, the node can be omitted.
        """
        self.node = node
        super().__init__(filename)
        self.ensureSanity(self.ds_list, self.rra_list, step=60)

    @property
    def imagename(self):
        return os.path.basename(self.filename).rsplit('.', 2)[0] + ".png"

    def update(self):
        values = {
            'upstate': 1,
            'clients': float(len(self.node.get('clients', []))),
            'neighbors': float(len(self.node.get('neighbors', []))),
            'vpn_neighbors': float(len(self.node.vpn_neighbors)),
            'loadavg': float(self.node['statistics']['loadavg']),
        }
        for item in ('rx', 'tx', 'mgmt_rx', 'mgmt_tx', 'forward'):
            try:
                values[item + '_bytes'] = int(self.node['statistics']['traffic'][item]['bytes'])
            except TypeError:
                pass
            try:
                values[item + '_packets'] = int(self.node['statistics']['traffic'][item]['packets'])
            except TypeError:
                pass
        super().update(values)

    def graph(self, directory, timeframe):
        """
        Create a graph in the given directory. The file will be named
        basename.png if the RRD file is named basename.rrd
        """
        args = ['rrdtool','graph', os.path.join(directory, self.imagename),
                '-s', '-' + timeframe ,
                '-w', '800',
                '-h', '400',
                '-l', '0',
                '-y', '1:1',
                'DEF:clients=' + self.filename + ':clients:AVERAGE',
                'VDEF:maxc=clients,MAXIMUM',
                'CDEF:c=0,clients,ADDNAN',
                'CDEF:d=clients,UN,maxc,UN,1,maxc,IF,*',
                'AREA:c#0F0:up\\l',
                'AREA:d#F00:down\\l',
                'LINE1:c#00F:clients connected\\l',
                ]
        subprocess.check_output(args)

class GlobalRRD(RRD):
    ds_list = [
        # Number of nodes available
        DS('nodes', 'GAUGE', 120, 0, float('NaN')),
        # Number of client available
        DS('clients', 'GAUGE', 120, 0, float('NaN')),
    ]
    rra_list = [
        RRA('AVERAGE', 0.5, 1, 120),    #  2 hours of 1 minute samples
        RRA('AVERAGE', 0.5, 60, 744),   # 31 days  of 1 hour   samples
        RRA('AVERAGE', 0.5, 1440, 1780),# ~5 years of 1 day    samples
    ]

    def __init__(self, filepath):
        super().__init__(filepath)
        self.ensureSanity(self.ds_list, self.rra_list, step=60)

    def update(self, nodeCount, clientCount):
        super().update({'nodes': nodeCount, 'clients': clientCount})

    def graph(self, filename, timeframe):
        args = ["rrdtool", 'graph', filename,
                '-s', '-' + timeframe,
                '-w', '800',
                '-h' '400',
                'DEF:nodes=' + self.filename + ':nodes:AVERAGE',
                'LINE1:nodes#F00:nodes\\l',
                'DEF:clients=' + self.filename + ':clients:AVERAGE',
                'LINE2:clients#00F:clients',
        ]
        subprocess.check_output(args)
