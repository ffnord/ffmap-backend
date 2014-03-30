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
        try:
          node_alias['gps'] = str(node['location']['latitude']) + ' ' + str(node['location']['longitude'])
        except:
          pass

      try:
        node_alias['firmware'] = node['software']['firmware']['release']
      except KeyError:
        pass

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
