# Data for Freifunk Map, Graph and Node List

[![Build Status](https://travis-ci.org/ffnord/ffmap-backend.svg?branch=master)](https://travis-ci.org/ffnord/ffmap-backend)

ffmap-backend gathers information on the batman network by invoking :

 * batctl (might require root),
 * alfred-json and
 * batadv-vis

The output will be written to a directory (`-d output`).

Copy `mkmap.sh-example` to `mkmap.sh` and adapt to your needs, test `backend.py` for example with: 

    backend.py -d /path/to/output -a /path/to/aliases.json --vpn ae:7f:58:7d:6c:2a d2:d0:93:63:f7:da

Run `backend.py --help` for a quick overview of all available options.

For the script's regular execution add the following file to cron in `/etc/cron.d/ffmap-backend`:
 
    MAILTO=example@your-NOC.org
    # Freifunk Map Updates
    PATH=/usr/sbin:/usr/bin:/sbin:/bin
    * * * * *       root nice -n 19 /path/to/mkmap.sh > /dev/null 2>&1
    # EOF

# Dependencies

- Python 3
- Python 3 Package [Networkx](https://networkx.github.io/)
- [alfred-json](https://github.com/tcatm/alfred-json)
- rrdtool (if run with `--with-rrd`)

# Install

on debian jessie:  

    apt-get install python3-networkx cmake libjansson-dev zlib1g-dev

on debian wheezy:

    apt-get install cmake libjansson-dev zlib1g-dev
    pip-3.2 install networkx

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

## Old data format

If you want to still use the old [ffmap-d3](https://github.com/ffnord/ffmap-d3)
front end, you can use the file `ffmap-d3.jq` to convert the new output to the
old one:

```
jq -n -f ffmap-d3.jq \
    --argfile nodes nodedb/nodes.json \
    --argfile graph nodedb/graph.json \
    > nodedb/ffmap-d3.json
```

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

     jq '.nodes = (.nodes | with_entries(del(.value.nodeinfo.owner)))' \
       < /ffmap-data/nodes.json > /var/www/data/nodes.json

This will remove owner information from nodes.json before copying the data
to your webserver.

[jq]: https://stedolan.github.io/jq/
