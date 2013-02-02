#!/usr/bin/env python3

import json
import argparse
from itertools import zip_longest
from urllib.request import urlopen
from bs4 import BeautifulSoup

def import_wikigps(url):
  def fetch_wikitable(url):
    f = urlopen(url)

    soup = BeautifulSoup(f)

    table = soup.find_all("table")[0]

    rows = table.find_all("tr")

    headers = []

    data = []

    def maybe_strip(x):
      if isinstance(x.string, str):
        return x.string.strip()
      else:
        return ""

    for row in rows:
      tds = list([maybe_strip(x) for x in row.find_all("td")])
      ths = list([maybe_strip(x) for x in row.find_all("th")])

      if any(tds):
        data.append(tds)

      if any(ths):
        headers = ths

    nodes = []

    for d in data:
      nodes.append(dict(zip(headers, d)))

    return nodes

  nodes = fetch_wikitable(url)

  aliases = {}

  for node in nodes:
    try:
      node['MAC'] = node['MAC'].split(',')
    except KeyError:
      pass

    try:
      node['GPS'] = node['GPS'].split(',')
    except KeyError:
      pass

    try:
      node['Knotenname'] = node['Knotenname'].split(',')
    except KeyError:
      pass

    nodes = zip_longest(node['MAC'], node['GPS'], node['Knotenname'])

    for data in nodes:
      alias = {}

      mac = data[0].strip()

      if data[1]:
        alias['gps'] = data[1].strip()

      if data[2]:
        alias['name'] = data[2].strip()

      aliases[mac] = alias

  return aliases

parser = argparse.ArgumentParser()

parser.add_argument('url', help='wiki URL')

args = parser.parse_args()

options = vars(args)

aliases = import_wikigps(options['url'])

print(json.dumps(aliases))
