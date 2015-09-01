import socket
import time


class Graphite(object):

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = int(port)

    def flatten_dict(self, d):
        def expand(key, value):
            if isinstance(value, dict):
                return [('{}.{}'.format(key, k), v) for k, v in self.flatten_dict(value).items()]
            else:
                return [(key, value)]
        items = [item for k, v in d.items() for item in expand(k, v)]
        return dict(items)

    def update(self, prefix, metrics, nodes):
        timestamp = int(time.time())

        sock = socket.socket()
        sock.connect((self.hostname, self.port))

        for node in nodes:
            try:
                if node['flags']['online']:
                    stats = self.flatten_dict(node['statistics'])
                    for metric in metrics.split(','):
                        try:
                            msg = '{}{}.{} {} {}\n'.format(
                                prefix,
                                node['nodeinfo']['node_id'].replace(' ', '_'),
                                metric.replace(' ', '_'),
                                stats[metric],
                                timestamp
                            )
                            sock.send(msg.encode('utf-8'))

                        except KeyError:
                            pass

            except KeyError:
                pass

        sock.close()
