#!/usr/bin/env python3
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

def aliases():
  alias = {}
  for node in nodeinfo():
    node_alias = {}
    if 'location' in node:
      try:
        node_alias['gps'] = str(node['location']['latitude']) + ' ' + str(node['location']['longitude'])
      except:
        pass

    try:
      node_alias['firmware'] = node['software']['firmware']['release']
    except KeyError:
      pass

    try:
      node_alias['id'] = node['network']['mac']
    except KeyError:
      pass

    if 'hostname' in node:
      node_alias['name'] = node['hostname']
    elif 'name' in node:
      node_alias['name'] = node['name']
    if len(node_alias):
      alias[node['network']['mac']] = node_alias

  return alias
