import subprocess
import json

class Input:
    """Fill the NodeDB with links from batadv-vis.

    The links are added as lists containing the neighboring nodes, not
    only their identifiers!  Mind this when exporting the database, as
    it probably leads to recursion.
    """
    def __init__(self, mesh_interface="bat0"):
        self.mesh_interface = mesh_interface

    @staticmethod
    def _is_similar_mac(a, b):
        """Determine if two MAC addresses are similar."""
        if a == b:
            return True

        # Split the address into bytes
        try:
            mac_a = list(int(i, 16) for i in a.split(":"))
            mac_b = list(int(i, 16) for i in b.split(":"))
        except ValueError:
            return False

        # Second and third byte musn't differ
        if mac_a[1] != mac_b[1] or mac_a[2] != mac_b[2]:
            return False

        # First byte must only differ in bit 2
        if mac_a[0] | 2 != mac_b[0] | 2:
            return False

        # Count differing bytes after the third
        c = [x for x in zip(mac_a[3:], mac_b[3:]) if x[0] != x[1]]

        # No more than two additional bytes must differ
        if len(c) > 2:
            return False

        # If no more bytes differ, they are very similar
        if len(c) == 0:
            return True

        # If the sum of absolute differences isn't greater than 2, they
        # are pretty similar
        delta = sum(abs(i[0] - i[1]) for i in c)
        return delta < 2

    def get_data(self, nodedb):
        """Add data from batadv-vis to the supplied nodedb"""
        output = subprocess.check_output([
            "batadv-vis",
            "-i", str(self.mesh_interface),
            "-f", "jsondoc",
        ])
        data = json.loads(output.decode("utf-8"))

        # First pass
        for node in data["vis"]:
            # Determine possible other MAC addresses of this node by
            # comparing all its client's MAC addresses to its primary
            # MAC address.  If they are similar, it probably is another
            # address of the node itself!  If it isn't, it is a real
            # client.
            node['aliases'] = [node["primary"]]
            if 'secondary' in node:
                node['aliases'].extend(node['secondary'])
            real_clients = []
            for mac in node["clients"]:
                if self._is_similar_mac(mac, node["primary"]):
                    node['aliases'].append(mac)
                else:
                    real_clients.append(mac)
            node['clients'] = real_clients

            # Add nodes and aliases without any information at first.
            # This way, we can later link the objects themselves.
            nodedb.add_or_update(node['aliases'])

        # Second pass
        for node in data["vis"]:
            # We only need the primary address now, all aliases are
            # already present in the database.  Furthermore, we can be
            # sure that all neighbors are in the database as well.  If
            # a neighbor isn't added already, we simply ignore it.
            nodedb.add_or_update(
                [node["primary"]],
                {
                    "clients": node["clients"],
                    "neighbors": [
                        {
                            "metric": neighbor['metric'],
                            "neighbor": nodedb[neighbor['neighbor']],
                        } for neighbor in node["neighbors"]
                          if neighbor['neighbor'] in nodedb
                    ]
                }
            )
