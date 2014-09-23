import subprocess
import json

class Input:
    def __init__(self,request_data_type = 158):
        self.request_data_type = request_data_type

    @staticmethod
    def _call_alfred(request_data_type):
        return json.loads(subprocess.check_output([
            "alfred-json",
            "-z",
            "-r", str(request_data_type),
            "-f", "json",
        ]).decode("utf-8"))

    def get_data(self, nodedb):
        """Add data from alfred to the supplied nodedb"""
        nodeinfo = self._call_alfred(self.request_data_type)
        statistics = self._call_alfred(self.request_data_type+1)

        # merge statistics into nodeinfo to be compatible with earlier versions
        for mac, node in statistics.items():
            if mac in nodeinfo:
                nodeinfo[mac]['statistics'] = statistics[mac]

        for mac, node in nodeinfo.items():
            aliases = [mac] + node.get('network', {}).get('mesh_interfaces', [])
            nodedb.add_or_update(aliases, node)
