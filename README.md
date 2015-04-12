# Data for Freifunk Map, Graph and Node List

[![Build Status](https://travis-ci.org/ffnord/ffmap-backend.svg?branch=master)](https://travis-ci.org/ffnord/ffmap-backend)

ffmap-backend gathers information on the batman network by invoking :

 * batctl (might require root),
 * alfred-json and
 * batadv-vis

The output will be written to a directory (`-d output`).

Run `backend.py --help` for a quick overview of all available options.

For the script's regular execution add the following to the crontab:

<pre>
* * * * * backend.py -d /path/to/output -a /path/to/aliases.json --vpn ae:7f:58:7d:6c:2a d2:d0:93:63:f7:da
</pre>

# Running as unprivileged user

Some information collected by ffmap-backend requires access to specific system resources.

Make sure the user you are running this under is part of the group that owns the alfred socket, so
alfred-json can access the alfred daemon.

    # ls -al /var/run/alfred.sock
    srw-rw---- 1 root alfred 0 Mar 19 22:00 /var/run/alfred.sock=
    # adduser map alfred
    Adding user `map' to group `alfred' ...
    Adding user map to group alfred
    Done.
    $ groups
    map alfred

Running batctl requires passwordless sudo access, because it needs to access the debugfs to retrive
the gateway list.

    # echo 'map ALL = NOPASSWD: /usr/sbin/batctl' | tee /etc/sudoers.d/map
    map ALL = NOPASSWD: /usr/sbin/batctl
    # chmod 0440 /etc/sudoers.d/map

That should be everything. The script automatically detects if it is run in unprivileged mode and
will prefix `sudo` where necessary.

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

# Removing owner information

If you'd like to redact information about the node owner from `nodes.json`,
you may use a filter like [jq]. In this case, specify an output directory
different from your webserver directory, e.g.:

    ./backend.py -d /ffmap-data

Don't write to files generated in there. ffmap-backend uses them as its
database.

After running ffmap-backend, copy `graph.json` to your webserver. Then,
filter `nodes.json` using `jq` like this:

     jq '.nodes = (.nodes | with_entries(del(.value.nodeinfo.owner)))' \
       < /ffmap-data/nodes.json > /var/www/data/nodes.json

This will remove owner information from nodes.json before copying the data
to your webserver.

[jq]: https://stedolan.github.io/jq/
