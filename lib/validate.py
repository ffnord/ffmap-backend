import json


def validate_nodeinfos(nodeinfos):
    result = []

    for nodeinfo in nodeinfos:
        if validate_nodeinfo(nodeinfo):
            result.append(nodeinfo)

    return result


def validate_nodeinfo(nodeinfo):
    if 'location' in nodeinfo:
        if 'latitude' not in nodeinfo['location'] or 'longitude' not in nodeinfo['location']:
            return False

    return True
