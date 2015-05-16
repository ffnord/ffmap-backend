{
    "meta": {
        "timestamp": $nodes.timestamp
    },
    "nodes": (
        $graph.batadv.nodes
        | map(
            if has("node_id") and .node_id
            then (
                $nodes.nodes[.node_id] as $node
                | {
                    "id": .id,
                    "uptime": $node.statistics.uptime,
                    "flags": ($node.flags + {"client": false}),
                    "name": $node.nodeinfo.hostname,
                    "clientcount": (if $node.statistics.clients >= 0 then $node.statistics.clients else 0 end),
                    "hardware": $node.nodeinfo.hardware.model,
                    "firmware": $node.nodeinfo.software.firmware.release,
                    "geo": (if $node.nodeinfo.location then [$node.nodeinfo.location.latitude, $node.nodeinfo.location.longitude] else null end),
                    #"lastseen": $node.lastseen,
                    "network": $node.nodeinfo.network
                }
            )
            else
                {
                    "flags": {},
                    "id": .id,
                    "geo": null,
                    "clientcount": 0
                }
            end
        )
    ),
    "links": (
        $graph.batadv.links
        | map(
            $graph.batadv.nodes[.source].node_id as $source_id
            | $graph.batadv.nodes[.target].node_id as $target_id
            | select(
                $source_id and $target_id and
                ($nodes.nodes | (has($source_id) and has($target_id)))
            )
            | {
                "target": .target,
                "source": .source,
                "quality": "\(.tq), \(.tq)",
                "id": ($source_id + "-" + $target_id),
                "type": (if .vpn then "vpn" else null end)
            }
        )
    )
}
