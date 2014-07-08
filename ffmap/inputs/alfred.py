import subprocess
import json

class Input:
    def __init__(self,request_data_type = 158):
        self.request_data_type = request_data_type

    def get_data(self, nodedb):
        """Add data from alfred to the supplied nodedb"""
        output = subprocess.check_output([
            "alfred-json",
            "-r", str(self.request_data_type),
            "-f", "json",
        ])
        alfred_data = json.loads(output.decode("utf-8"))

        for mac, node in alfred_data.items():
            nodedb.add_or_update([mac], node)
