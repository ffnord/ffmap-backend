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
      for key in node:
        node_alias[key] = node[key]

      try:
        node_alias['geo'] = [node['location']['latitude'], node['location']['longitude']]
      except (TypeError, KeyError):
        pass

      try:
        node_alias['id'] = node['network']['mac']
      except KeyError:
        pass

      if 'hostname' in node:
        node_alias['name'] = node['hostname']
      if len(node_alias):
        alias[mac] = node_alias
    return alias

if __name__ == "__main__":
  ad = alfred()
  al = ad.aliases()
  print(al)
