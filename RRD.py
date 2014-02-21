import subprocess
import re
import io
import os
from tempfile import TemporaryFile
from operator import xor, eq
from functools import reduce
from itertools import starmap
import math

class RRDIncompatibleException(Exception):
    """
    Is raised when an RRD doesn't have the desired definition and cannot be
    upgraded to it.
    """
    pass
class RRDOutdatedException(Exception):
    """
    Is raised when an RRD doesn't have the desired definition, but can be
    upgraded to it.
    """
    pass

if not hasattr(__builtins__, "FileNotFoundError"):
    class FileNotFoundError(Exception):
        pass

class RRD:
    """
    An RRD is a Round Robin Database, a database which forgets old data and
    aggregates multiple records into new ones.

    It contains multiple Data Sources (DS) which can be thought of as columns,
    and Round Robin Archives (RRA) which can be thought of as tables with the
    DS as columns and time-dependant rows.
    """

    # rra[2].cdp_prep[0].value = 1,8583033333e+03
    _info_regex = re.compile("""
            (?P<section>[a-z_]+)
            \[ (?P<key>[a-zA-Z0-9_]+) \]
            \.
        |
            (?P<name>[a-z_]+)
            \s*=\s*
            "? (?P<value>.*?) "?
        $""", re.X)
    _cached_info = None

    def _exec_rrdtool(self, cmd, *args, **kwargs):
        pargs = ["rrdtool", cmd, self.filename]
        for k,v in kwargs.items():
            pargs.extend(["--" + k, str(v)])
        pargs.extend(args)
        subprocess.check_output(pargs)

    def __init__(self, filename):
        self.filename = filename

    def ensureSanity(self, ds_list, rra_list, **kwargs):
        """
        Create or upgrade the RRD file if necessary to contain all DS in
        ds_list. If it needs to be created, the RRAs in rra_list and any kwargs
        will be used for creation. Note that RRAs and options of an existing
        database are NOT modified!
        """
        try:
            self.checkSanity(ds_list)
        except FileNotFoundError:
            self.create(ds_list, rra_list, **kwargs)
        except RRDOutdatedException:
            self.upgrade(ds_list)

    def checkSanity(self, ds_list=()):
        """
        Check if the RRD file exists and contains (at least) the DS listed in
        ds_list.
        """
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)
        info = self.info()
        if set(ds_list) - set(info['ds'].values()) != set():
            if set((ds.name, ds.type) for ds in ds_list) \
             - set((ds.name, ds.type) for ds in info['ds'].values()) != set():
                raise RRDIncompatibleException()
            else:
                raise RRDOutdatedException()

    def upgrade(self, dss):
        """
        Upgrade the DS definitions (!) of this RRD.
        (To update its values, use update())

        The list dss contains DSS objects to be updated or added. The
        parameters of a DS can be changed, but not its type. New DS are always
        added at the end in the order of their appearance in the list.

        This is done internally via an rrdtool dump -> rrdtool restore and
        modifying the dump on the fly.
        """
        info = self.info()
        new_ds = list(info['ds'].values())
        new_ds.sort(key=lambda ds: ds.index)
        for ds in dss:
            if ds.name in info['ds']:
                old_ds = info['ds'][ds.name]
                if info['ds'][ds.name].type != ds.type:
                    raise RuntimeError('Cannot convert existing DS "%s" from type "%s" to "%s"' %
                        (ds.name, old_ds.type, ds.type))
                ds.index = old_ds.index
                new_ds[ds.index] = ds
            else:
                ds.index = len(new_ds)
                new_ds.append(ds)
        added_ds_num = len(new_ds) - len(info['ds'])

        dump = subprocess.Popen(
            ["rrdtool", "dump", self.filename],
            stdout=subprocess.PIPE
        )
        restore = subprocess.Popen(
            ["rrdtool", "restore", "-", self.filename + ".new"],
            stdin=subprocess.PIPE
        )
        echo = True
        ds_definitions = True
        for line in dump.stdout:
            if ds_definitions and b'<ds>' in line:
                echo = False
            if b'<!-- Round Robin Archives -->' in line:
                ds_definitions = False
                for ds in new_ds:
                    restore.stdin.write(bytes("""
                        <ds>
                           <name> %s </name>
                           <type> %s </type>
                           <minimal_heartbeat>%i</minimal_heartbeat>
                           <min>%s</min>
                           <max>%s</max>

                           <!-- PDP Status -->
                           <last_ds>%s</last_ds>
                           <value>%s</value>
                           <unknown_sec> %i </unknown_sec>
                        </ds>
                        """ % (
                            ds.name,
                            ds.type,
                            ds.args[0],
                            ds.args[1],
                            ds.args[2],
                            ds.last_ds,
                            ds.value,
                            ds.unknown_sec)
                    , "utf-8"))

            if b'</cdp_prep>' in line:
                restore.stdin.write(added_ds_num*b"""
                        <ds>
                        <primary_value> NaN </primary_value>
                        <secondary_value> NaN </secondary_value>
                        <value> NaN </value>
                        <unknown_datapoints> 0 </unknown_datapoints>
                        </ds>
                """)

            # echoing of input line
            if echo:
                restore.stdin.write(
                    line.replace(
                        b'</row>',
                        (added_ds_num*b'<v>NaN</v>')+b'</row>'
                    )
                )

            if ds_definitions and b'</ds>' in line:
                echo = True
        dump.stdout.close()
        restore.stdin.close()
        try:
            dump.wait(1)
        except subprocess.TimeoutExpired:
            dump.kill()
        try:
            restore.wait(2)
        except subprocess.TimeoutExpired:
            dump.kill()
            raise RuntimeError("rrdtool restore process killed")

        os.rename(self.filename + ".new", self.filename)
        self._cached_info = None

    def create(self, ds_list, rra_list, **kwargs):
        """
        Create a new RRD file with the specified list of RRAs and DSs.

        Any kwargs are passed as --key=value to rrdtool create.
        """
        self._exec_rrdtool(
            "create",
            *map(str, rra_list + ds_list),
            **kwargs
        )
        self._cached_info = None

    def update(self, V):
        """
        Update the RRD with new values V.

        V can be either list or dict:
        * If it is a dict, its keys must be DS names in the RRD and it is
          ensured that the correct DS are updated with the correct values, by
          passing a "template" to rrdtool update (see man rrdupdate).
        * If it is a list, no template is generated and the order of the
          values in V must be the same as that of the DS in the RRD.
        """
        try:
            args = ['N:' + ':'.join(map(str, V.values()))]
            kwargs = {'template': ':'.join(V.keys())}
        except AttributeError:
            args = ['N:' + ':'.join(map(str, V))]
            kwargs = {}
        self._exec_rrdtool("update", *args, **kwargs)
        self._cached_info = None

    def info(self):
        """
        Return a dictionary with information about the RRD.

        See `man rrdinfo` for more details.
        """
        if self._cached_info:
            return self._cached_info
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        proc = subprocess.Popen(
            ["rrdtool", "info", self.filename],
            stdout=subprocess.PIPE,
            env=env
        )
        out, err = proc.communicate()
        out = out.decode()
        info = {}
        for line in out.splitlines():
            base = info
            for match in self._info_regex.finditer(line):
                section, key, name, value = match.group("section", "key", "name", "value")
                if section and key:
                    try:
                        key = int(key)
                    except ValueError:
                        pass
                    if section not in base:
                        base[section] = {}
                    if key not in base[section]:
                        base[section][key] = {}
                    base = base[section][key]
                if name and value:
                    try:
                        base[name] = int(value)
                    except ValueError:
                        try:
                            base[name] = float(value)
                        except:
                            base[name] = value
        dss = {}
        for name, ds in info['ds'].items():
            ds_obj = DS(name, ds['type'], ds['minimal_heartbeat'], ds['min'], ds['max'])
            ds_obj.index = ds['index']
            ds_obj.last_ds = ds['last_ds']
            ds_obj.value = ds['value']
            ds_obj.unknown_sec = ds['unknown_sec']
            dss[name] = ds_obj
        info['ds'] = dss
        rras = []
        for rra in info['rra'].values():
            rras.append(RRA(rra['cf'], rra['xff'], rra['pdp_per_row'], rra['rows']))
        info['rra'] = rras
        self._cached_info = info
        return info

class DS:
    """
    DS stands for Data Source and represents one line of data points in a Round
    Robin Database (RRD).
    """
    name = None
    type = None
    args = []
    index = -1
    last_ds = 'U'
    value = 0
    unknown_sec = 0
    def __init__(self, name, dst, *args):
        self.name = name
        self.type = dst
        self.args = args

    def __str__(self):
        return "DS:%s:%s:%s" % (
            self.name,
            self.type,
            ":".join(map(str, self._nan_to_U_args()))
        )

    def __repr__(self):
        return "%s(%r, %r, %s)" % (
            self.__class__.__name__,
            self.name,
            self.type,
            ", ".join(map(repr, self.args))
        )

    def __eq__(self, other):
        return all(starmap(eq, zip(self._compare_keys(), other._compare_keys())))

    def __hash__(self):
        return reduce(xor, map(hash, self._compare_keys()))

    def _nan_to_U_args(self):
        return tuple(
            'U' if type(arg) is float and math.isnan(arg)
            else arg
            for arg in self.args
        )

    def _compare_keys(self):
        return (self.name, self.type, self._nan_to_U_args())

class RRA:
    def __init__(self, cf, *args):
        self.cf = cf
        self.args = args

    def __str__(self):
        return "RRA:%s:%s" % (self.cf, ":".join(map(str, self.args)))

    def __repr__(self):
        return "%s(%r, %s)" % (
            self.__class__.__name__,
            self.cf,
            ", ".join(map(repr, self.args))
        )
