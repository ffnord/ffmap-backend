def export_nodelist(now, nodedb):
    nodelist = list()

    for node_id, node in nodedb["nodes"].items():
        node_out = dict()
        node_out["id"] = node_id
        node_out["name"] = node["nodeinfo"]["hostname"]

        if "location" in node["nodeinfo"]:
            node_out["position"] = {"lat": node["nodeinfo"]["location"]["latitude"],
                                    "long": node["nodeinfo"]["location"]["longitude"]}

        node_out["status"] = dict()
        node_out["status"]["online"] = node["flags"]["online"]

        if "firstseen" in node:
            node_out["status"]["firstcontact"] = node["firstseen"]

        if "lastseen" in node:
            node_out["status"]["lastcontact"] = node["lastseen"]

        if "clients" in node["statistics"]:
            node_out["status"]["clients"] = node["statistics"]["clients"]

        nodelist.append(node_out)

    return {"version": "1.0.1", "nodes": nodelist, "updated_at": now.isoformat()}
