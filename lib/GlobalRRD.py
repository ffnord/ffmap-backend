import os
import subprocess

from lib.RRD import DS, RRA, RRD


class GlobalRRD(RRD):
    ds_list = [
        # Number of nodes available
        DS('nodes', 'GAUGE', 120, 0, float('NaN')),
        # Number of client available
        DS('clients', 'GAUGE', 120, 0, float('NaN')),
    ]
    rra_list = [
        # 2 hours of 1 minute samples
        RRA('AVERAGE', 0.5, 1, 120),
        # 31 days  of 1 hour samples
        RRA('AVERAGE', 0.5, 60, 744),
        # ~5 years of 1 day samples
        RRA('AVERAGE', 0.5, 1440, 1780),
    ]

    def __init__(self, directory):
        super().__init__(os.path.join(directory, "nodes.rrd"))
        self.ensure_sanity(self.ds_list, self.rra_list, step=60)

    # TODO: fix this, python does not support function overloading
    def update(self, node_count, client_count):
        super().update({'nodes': node_count, 'clients': client_count})

    def graph(self, filename, timeframe):
        args = ["rrdtool", 'graph', filename,
                '-s', '-' + timeframe,
                '-w', '800',
                '-h' '400',
                'DEF:nodes=' + self.filename + ':nodes:AVERAGE',
                'LINE1:nodes#F00:nodes\\l',
                'DEF:clients=' + self.filename + ':clients:AVERAGE',
                'LINE2:clients#00F:clients']
        subprocess.check_output(args)
