import subprocess
import json
import re


class Batman(object):
    """
    Bindings for B.A.T.M.A.N. Advanced
    commandline interface "batctl"
    """
    def __init__(self, mesh_interface='bat0'):
        self.mesh_interface = mesh_interface

    def vis_data(self, batadv_vis=False):
        vds = self.vis_data_batctl_legacy()
        if batadv_vis:
            vds += self.vis_data_batadv_vis()
        return vds

    @staticmethod
    def vis_data_helper(lines):
        vd_tmp = []
        for line in lines:
            try:
                utf8_line = line.decode('utf-8')
                vd_tmp.append(json.loads(utf8_line))
            except UnicodeDecodeError:
                pass
        return vd_tmp

    def vis_data_batctl_legacy(self):
        """
        Parse "batctl -m <mesh_interface> vd json -n" into an array of dictionaries.
        """
        output = subprocess.check_output(['batctl', '-m', self.mesh_interface, 'vd', 'json', '-n'])
        lines = output.splitlines()
        vds = self.vis_data_helper(lines)
        return vds

    def vis_data_batadv_vis(self):
        """
        Parse "batadv-vis -i <mesh_interface> -f json" into an array of dictionaries.
        """
        output = subprocess.check_output(['batadv-vis', '-i', self.mesh_interface, '-f', 'json'])
        lines = output.splitlines()
        return self.vis_data_helper(lines)

    def gateway_list(self):
        """
        Parse "batctl -m <mesh_interface> gwl -n" into an array of dictionaries.
        """
        output = subprocess.check_output(['batctl', '-m', self.mesh_interface, 'gwl', '-n'])
        output_utf8 = output.decode('utf-8')
        lines = output_utf8.splitlines()

        own_mac = re.match(r"^.*MainIF/MAC: [^/]+/([0-9a-f:]+).*$", lines[0]).group(1)

        gateways = []
        gw_mode = self.gateway_mode()
        if gw_mode['mode'] == 'server':
            gateways.append(own_mac)

        for line in lines:
            gw_line = re.match(r"^(?:=>)? +([0-9a-f:]+) ", line)
            if gw_line:
                gateways.append(gw_line.group(1))

        return gateways

    def gateway_mode(self):
        """
        Parse "batctl -m <mesh_interface> gw"
        """
        output = subprocess.check_output(['batctl', '-m', self.mesh_interface, 'gw'])
        elements = output.decode("utf-8").split()
        mode = elements[0]
        if mode == 'server':
            return {'mode': 'server',
                    'bandwidth': elements[3]}
        else:
            return {'mode': mode}

if __name__ == "__main__":
    bc = Batman()
    vd = bc.vis_data()
    gw = bc.gateway_list()
    for x in vd:
        print(x)
    print(gw)
    print(bc.gateway_mode())
