import json
import argparse
from itertools import zip_longest
from urllib.request import urlopen
from bs4 import BeautifulSoup

class Input:
    def __init__(self, url="http://luebeck.freifunk.net/wiki/Knoten"):
        self.url = url

    def fetch_wikitable(self):
        f = urlopen(self.url)
        soup = BeautifulSoup(f)
        table = soup.find("table")
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

        return [dict(zip(headers, d)) for d in data]

    def get_data(self, nodedb):
        nodes = self.fetch_wikitable()

        for node in nodes:
            if "MAC" not in node or not node["MAC"]:
                # without MAC, we cannot merge this data with others, so
                # we might as well ignore it
                continue

            newnode = {
                "network": {
                    "mac": node.get("MAC").lower(),
                },
                "location": {
                    "latitude": float(node.get("GPS", " ").split(" ")[0]),
                    "longitude": float(node.get("GPS", " ").split(" ")[1]),
                    "description": node.get("Ort"),
                } if " " in node.get("GPS", "") else None,
                "hostname": node.get("Knotenname"),
                "hardware": {
                    "model": node["Router"],
                } if node.get("Router") else None,
                "software": {
                    "firmware": {
                        "base": "LFF",
                        "release": node.get("LFF Version"),
                    },
                },
                "owner": {
                    "contact": node["Betreiber"],
                } if node.get("Betreiber") else None,
            }
            # remove keys with None as value
            newnode = {k: v for k,v in newnode.items() if v is not None}
            nodedb.add_or_update([newnode["network"]["mac"]], newnode)
