import numpy as np

SNAP_DIST = 15


def _snap_nodes(segments):
    nodes = []
    mapping = {}
    endpoints = []
    for seg in segments:
        endpoints.append((seg["x1"], seg["y1"]))
        endpoints.append((seg["x2"], seg["y2"]))

    for i, pt in enumerate(endpoints):
        matched = None
        for j, node in enumerate(nodes):
            if np.hypot(pt[0] - node[0], pt[1] - node[1]) < SNAP_DIST:
                matched = j
                break
        if matched is None:
            matched = len(nodes)
            nodes.append(pt)
        mapping[i] = matched

    return nodes, mapping


def build_graph(segments):
    nodes_raw, mapping = _snap_nodes(segments)

    degree = [0] * len(nodes_raw)
    edges  = []

    for i, seg in enumerate(segments):
        na = mapping[i * 2]
        nb = mapping[i * 2 + 1]
        if na == nb:
            continue
        degree[na] += 1
        degree[nb] += 1
        edges.append({
            "id": i,
            "node_a": na, "node_b": nb,
            "x1": seg["x1"], "y1": seg["y1"],
            "x2": seg["x2"], "y2": seg["y2"],
            "length": seg["length"],
            "angle":  seg["angle"]
        })

    def node_type(d):
        if d == 1: return "endpoint"
        if d == 2: return "corner"
        if d == 3: return "t-junction"
        return "x-junction"

    nodes = [{"id": i, "x": int(nodes_raw[i][0]), "y": int(nodes_raw[i][1]),
               "degree": degree[i], "type": node_type(degree[i])}
             for i in range(len(nodes_raw))]

    return nodes, edges


def classify_walls(nodes, edges, image_w, image_h, margin=0.12):
    mx = image_w * margin
    my = image_h * margin
    node_map = {n["id"]: n for n in nodes}
    lengths  = [e["length"] for e in edges]
    spine_th = np.percentile(lengths, 75) if lengths else 0

    classified = []
    for e in edges:
        na = node_map[e["node_a"]]
        nb = node_map[e["node_b"]]

        def near(n):
            return n["x"] <= mx or n["x"] >= image_w - mx or \
                   n["y"] <= my or n["y"] >= image_h - my

        if near(na) and near(nb):
            cls = "load_bearing_outer"
        elif e["length"] >= spine_th:
            cls = "load_bearing_spine"
        else:
            cls = "partition"

        classified.append({**e, "wall_class": cls})

    return classified
