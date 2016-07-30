# Data for Freifunk Map, Graph and Node List

[![Build Status](https://travis-ci.org/ffnord/ffmap-backend.svg?branch=master)](https://travis-ci.org/ffnord/ffmap-backend)

ffmap-backend gathers information on the batman network by invoking :

 * batctl (might require root),
 * alfred-json and
 * batadv-vis

The output will be written to a directory (`-d output`).

Run `backend.py --help` for a quick overview of all available options.

For the script's regular execution add the following to the crontab:

    * * * * * backend.py -d /path/to/output -a /path/to/aliases.json --vpn ae:7f:58:7d:6c:2a d2:d0:93:63:f7:da

# Dependencies

- Python 3
- Python 3 Package [Networkx](https://networkx.github.io/)
    (on debian wheezy: pip-3.2 install networkx)
- [alfred-json](https://github.com/tcatm/alfred-json)
- rrdtool (if run with `--with-rrd`)

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

    { "nodes": [
        { "flags": { flags },
          "firstseen": isoformat,
          "lastseen": isoformat,
          "nodeinfo": {...},         # copied from node's nodeinfo announcement
          "statistics": {
             "uptime": double,       # seconds
             "memory_usage": double, # 0..1
             "clients": double,
             "rootfs_usage": double, # 0..1
             "loadavg": double,
             "gateway": mac
           }
        },
        ...
      ]
      "timestamp": isoformat,
      "version": 2
    }

### flags (bool)

- online
- gateway

## Old data format

If you want to still use the old [ffmap-d3](https://github.com/ffnord/ffmap-d3)
front end, you can use the file `ffmap-d3.jq` to convert the new output to the
old one:

    jq -n -f ffmap-d3.jq \
        --argfile nodes nodedb/nodes.json \
        --argfile graph nodedb/graph.json \
        > nodedb/ffmap-d3.json


Then point your ffmap-d3 instance to the `ffmap-d3.json` file.

# Removing owner information

If you'd like to redact information about the node owner from `nodes.json`,
you may use a filter like [jq]. In this case, specify an output directory
different from your webserver directory, e.g.:

    ./backend.py -d /ffmap-data

Don't write to files generated in there. ffmap-backend uses them as its
database.

After running ffmap-backend, copy `graph.json` to your webserver. Then,
filter `nodes.json` using `jq` like this:

    jq '.nodes = (.nodes | map(del(.nodeinfo.owner)))' \
        < /ffmap-data/nodes.json > /var/www/data/nodes.json

This will remove owner information from nodes.json before copying the data
to your webserver.

[jq]: https://stedolan.github.io/jq/


# Convert from nodes.json version 1 to version 2

    jq '.nodes = (.nodes | to_entries | map(.value)) | .version = 2' \
        < nodes.json > nodes.json.new
    mv nodes.json.new nodes.json


# Graphite support

## Comand line arguments
Running `backend.py` with `--with-graphite` will enable graphite support for storing statistical data.

    graphite integration:
      --with-graphite       Send statistical data to graphite backend
      --graphite-host GRAPHITE_HOST
                            Hostname of the machine running graphite
      --graphite-port GRAPHITE_PORT
                            Port of the carbon daemon
      --graphite-prefix GRAPHITE_PREFIX
                            Storage prefix (default value: 'freifunk.nodes.')
      --graphite-metrics GRAPHITE_METRICS
                            Comma separated list of metrics to store (default
                            value: 'clients,loadavg,uptime')

## Graphite configuration

### storage-schemas.conf

    [freifunk_node_stats]
    pattern = ^freifunk\.nodes\.
    retentions = 60s:1d,5min:7d,1h:30d,1d:4y

### storage-aggregation.conf

    [freifunk_node_stats_loadavg]
    pattern = ^freifunk\.nodes\..*\.loadavg$
    aggregationMethod = avg

    [freifunk_node_stats_clients]
    pattern = ^freifunk\.nodes\..*\.clients$
    aggregationMethod = max

    [freifunk_node_stats_uptime]
    pattern = ^freifunk\.nodes\..*\.uptime$
    aggregationMethod = last
