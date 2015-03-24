# Data for Freifunk Map, Graph and Node List

[![Build Status](https://travis-ci.org/ffnord/ffmap-backend.svg?branch=master)](https://travis-ci.org/ffnord/ffmap-backend)

ffmap-backend gathers information on the batman network by invoking 

 * batctl,
 * alfred-json and
 * batadv-vis

as root (via sudo) and has this information placed into a target directory
as the file "nodes.json" and also updates the directory "nodes" with graphical
representations of uptimes and the number of clients connecting.

Run `backend.py --help` for a quick overview of all available options.

When executed without root privileges, we suggest to grant sudo permissions
within wrappers of those binaries, so no further changes are required in other
scripts:

<pre>
$ cat <<EOCAT > $HOME/batctl
#!/bin/sh
exec sudo /usr/sbin/batctl $*
EOCAT
</pre>

and analogously for batadv-vis. The entry for /etc/sudoers could be
whateveruser   ALL=(ALL:ALL) NOPASSWD: /usr/sbin/batctl,/usr/sbin/batadv-vis,/usr/sbin/alfred-json

For the script's regular execution add the following to the crontab:
<pre>
* * * * * /path/to/ffmap-backend/backend.py -d /path/to/output -a /path/to/aliases.json --vpn ae:7f:58:7d:6c:2a --vpn d2:d0:93:63:f7:da
</pre>

# Data format

## nodes.json

    { 'nodes': {
        node_id: { 'flags': { flags },
                   'firstseen': isoformat,
                   'lastseen': isoformat,
                   'nodeinfo': {...},         # copied from alfred type 158
                   'statistics': {
                      'uptime': double,       # seconds
                      'memory_usage': double, # 0..1
                      'clients': double,
                      'rootfs_usage': double, # 0..1
                      'loadavg': double,
                      'gateway': mac
                    }
                 },
        ...
      }
      'timestamp': isoformat
    }

### flags (bool)

- online
- gateway
