#!/usr/bin/env python3
import subprocess
import json

class alfred:
  def __init__(self,request_data_type = 158):
    self.request_data_type = request_data_type

  def aliases(self):
    output = subprocess.check_output(["alfred-json","-r",str(self.request_data_type),"-f","json"])
    alfred_data = json.loads(output.decode("utf-8"))
    alias = {}
    for mac,node in alfred_data.items():
      node_alias = {}
      if 'location' in node:
        if 'latitude' in node['location'] and 'longitude' in node['location']:
          node_alias['gps'] = str(node['location']['latitude']) + ' ' + str(node['location']['longitude'])

      if 'software' in node:

        if 'firmware' in node['software']:
          if 'base' in node['software']['firmware']:
            node_alias['firmware-base'] = node['software']['firmware']['base']
          if 'release' in node['software']['firmware']:
            node_alias['firmware'] = node['software']['firmware']['release']

        if 'autoupdater' in node['software']:
          if 'branch' in node['software']['autoupdater']:
            node_alias['autoupdater-branch'] = node['software']['autoupdater']['branch']
          if 'enabled' in node['software']['autoupdater']:
            node_alias['autoupdater-enabled'] = node['software']['autoupdater']['enabled']

        if 'fastd' in node['software']:
          if 'enabled' in node['software']['fastd']:
            node_alias['fastd-enabled'] = node['software']['fastd']['enabled']
          if 'version' in node['software']['fastd']:
            node_alias['fastd-version'] = node['software']['fastd']['version']

      if 'hardware' in node:
        if 'model' in node['hardware']:
          node_alias['hardware-model'] = node['hardware']['model']

      if 'network' in node:
        if 'gateway' in node['network']:
          node_alias['selected-gateway'] = node['network']['gateway']

      if 'hostname' in node:
        node_alias['name'] = node['hostname']
      elif 'name' in node:
        node_alias['name'] = node['name']
      if len(node_alias):
        alias[mac] = node_alias
    return alias

if __name__ == "__main__":
  ad = alfred()
  al = ad.alias()
  print(al)
