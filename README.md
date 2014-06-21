ffmap-backend - Data for Freifunk Map

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

$ cat <<EOCAT > $HOME/batctl
#!/bin/sh
exec sudo /usr/sbin/batctl $*
EOCAT

and analogously for batadv-vis. The entry for /etc/sudoers could be
whateveruser   ALL=(ALL:ALL) NOPASSWD: /usr/sbin/batctl,/usr/sbin/batadv-vis,/usr/sbin/alfred-json

The destination directory can be made directly available through apache:

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
