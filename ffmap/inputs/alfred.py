import subprocess
import json

class Input:
    def __init__(self,request_data_type = 158):
        self.request_data_type = request_data_type

    def get_data(self, nodedb):
        """Add data from alfred to the supplied nodedb"""
        # get nodeinfo
        output = subprocess.check_output([
            "alfred-json",
            "-r", str(self.request_data_type),
            "-f", "json",
        ])
        nodeinfo = json.loads(output.decode("utf-8"))

        # get statistics
        output = subprocess.check_output([
            "alfred-json",
            "-r", str(self.request_data_type+1),
            "-f", "json",
        ])
        statistics = json.loads(output.decode("utf-8"))

        # merge statistics into nodeinfo to be compatible with earlier versions
        for mac, node in statistics.items():
            if mac in nodeinfo:
                nodeinfo[mac]['statistics'] = statistics[mac]

        for mac, node in nodeinfo.items():
            nodedb.add_or_update([mac], node)
