import subprocess
import json


def _fetch(data_type):
    output = subprocess.check_output(["alfred-json", "-z", "-f", "json", "-r", str(data_type)])
    return json.loads(output.decode("utf-8")).values()


def nodeinfo():
    return _fetch(158)


def statistics():
    return _fetch(159)


def vis():
    return _fetch(160)
