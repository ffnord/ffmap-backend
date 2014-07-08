# Data for Freifunk Map, Graph and Node List

ffmap-backend gathers information on the batman network by invoking
   batctl
and
   batadv-vis
as root (via sudo) and has this information placed into a target directory
as the file "nodes.json" and also updates the directory "nodes" with graphical
representations of uptimes and the number of clients connecting.

The target directory is suggested to host all information for interpreting those
node descriptions, e.g. as provided by https://github.com/ffnord/ffmap-d3.git .
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

The destination directory can be made directly available through apache:
<pre>
$ cat /etc/apache2/site-enabled/000-default
...
        <Directory /home/whateverusername/www/>
                Options Indexes FollowSymLinks MultiViews
                AllowOverride None
                Order allow,deny
                allow from all
        </Directory>
...

$ cat /etc/apache2/conf.d/freifunk
Alias /map /home/ffmap/www/
Alias /firmware /home/freifunk/autoupdates/
</pre>

To execute, run
 python3 -mffmap.run --input-alfred --input-badadv --output-d3json ../www/nodes.json
The script expects above described sudo-wrappers in the $HOME directory of the user executing
the script. If those are not available, an error will occurr if not executed as root. Also,
the tool realpath optionally allows to execute the script from anywhere in the directory tree.

For the script's regular execution add the following to the crontab:
<pre>
*/5 * * * * python3 -mffmap.run --input-alfred --input-badadv --output-d3json /home/ffmap/www/nodes.json
</pre>
