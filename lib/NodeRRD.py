import os
import subprocess

from lib.RRD import DS, RRA, RRD


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
        # 2 hours of  1 minute samples
        RRA('AVERAGE', 0.5, 1, 120),
        # 7 days  of  15 minute samples
        RRA('AVERAGE', 0.5, 15, 672),
    ]

    def __init__(self, filename, node=None, graph=None):
        """
        Create a new RRD for a given node.

        If the RRD isn't supposed to be updated, the node can be omitted.
        """
        self.node = node
        self.node_graph = graph
        super().__init__(filename)
        self.ensure_sanity(self.ds_list, self.rra_list, step=60)

    @property
    def imagename(self):
        return "{basename}.png".format(
            basename=os.path.basename(self.filename).rsplit('.', 2)[0])

    # TODO: fix this, python does not support function overloading
    def update(self):
        values = {
            'upstate': int(self.node['flags']['online']),
            'clients': float(self.node['statistics']['clients']),
            'loadavg': float(self.node['statistics'].get('loadavg', 0)),
        }
        for item in ('rx', 'tx', 'mgmt_rx', 'mgmt_tx', 'forward'):
            try:
                values.update({
                    ('%s_bytes' % item): int(self.node['statistics'].get('traffic', {}).get(item, {}).get('bytes', 0)),
                    ('%s_packets' % item): int(self.node['statistics'].get('traffic', {}).get(item, {}).get('packets', 0)),
                })
            except TypeError:
                pass
        try:
            graph_node = next(key for key, node in self.node_graph.nodes(data=True) if node.get('node_id') == self.node['nodeinfo']['node_id'])
            values.update({
                'neighbors': float(len(self.node_graph[graph_node])),
                'vpn_neighbors': float(len(list(filter(lambda edge: edge.get('vpn', False), self.node_graph[graph_node].values())))),
            })
        except StopIteration:
            pass
        super().update(values)

    def graph(self, directory, timeframe):
        """
        Create a graph in the given directory. The file will be named
        basename.png if the RRD file is named basename.rrd
        """
        args = ['rrdtool', 'graph', os.path.join(directory, self.imagename),
                '-s', '-' + timeframe,
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
                'LINE1:c#00F:clients connected\\l']
        subprocess.check_output(args)
