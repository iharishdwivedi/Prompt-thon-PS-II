import cv2
import numpy as np
import math

ANGLE_TOLERANCE = 10   # degrees — snap lines within ±10° of 0/90/180 to orthogonal
SNAP_DIST       = 12   # pixels — snap nearby endpoints to same node
PERIMETER_BAND  = 14   # pixels — thickness of perimeter mask


def _snap_angle(angle_deg):
    """
    Trap 1 fix: snap near-orthogonal angles to exact 0/90/-90/180.
    Prevents impossible geometries from slight angular deviations.
    """
    for target in [0, 90, -90, 180, -180]:
        if abs(angle_deg - target) <= ANGLE_TOLERANCE:
            return float(target)
    return angle_deg


def _snap_endpoint(x, y, node_list):
    """
    Trap 2 + 3 fix: snap endpoint to nearest existing node within SNAP_DIST.
    Prevents floating walls and open room boundaries from offset coordinates.
    Returns snapped (x, y) and node index.
    """
    for i, (nx, ny) in enumerate(node_list):
        if math.hypot(x - nx, y - ny) < SNAP_DIST:
            return nx, ny, i
    node_list.append((x, y))
    return x, y, len(node_list) - 1


def _classify_junction(node_id, degree):
    """
    Trap 2 fix: explicit junction type based on degree count.
    T-junction (3) and L-corner (2) are now correctly distinguished.
    """
    if degree == 1: return "endpoint"
    if degree == 2: return "corner"
    if degree == 3: return "t-junction"
    return "x-junction"


def parse(image_path):
    raw = open(image_path, 'rb').read()
    buf = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {image_path}")

    H, W = img.shape[:2]

    # ── CV Pipeline ──────────────────────────────────────────────
    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    closed  = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8), iterations=2)
    edges   = cv2.Canny(closed, 50, 150)

    # Outer perimeter contour
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    perimeter_mask = np.zeros((H, W), dtype=np.uint8)
    outer_contour  = None
    if contours:
        outer_contour = max(contours, key=cv2.contourArea)
        approx = cv2.approxPolyDP(outer_contour, 0.005 * cv2.arcLength(outer_contour, True), True)
        cv2.drawContours(perimeter_mask, [approx], -1, 255, PERIMETER_BAND)

    # Hough lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=40, maxLineGap=10)

    # ── Classification with all trap fixes ───────────────────────
    elements  = {"edges": [], "walls": [], "openings": [], "columns": [], "furniture": []}
    node_list = []   # shared snapped node pool
    degree    = {}   # node_id → connection count

    if lines is not None:
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]

            # Trap 1: snap angle to orthogonal grid
            raw_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            snapped   = _snap_angle(raw_angle)

            # If angle was snapped, reproject endpoint 2 along snapped direction
            if snapped != raw_angle:
                length_px = math.hypot(x2 - x1, y2 - y1)
                rad = math.radians(snapped)
                x2  = int(x1 + length_px * math.cos(rad))
                y2  = int(y1 + length_px * math.sin(rad))

            # Trap 3: snap endpoints to shared node pool
            x1, y1, na = _snap_endpoint(x1, y1, node_list)
            x2, y2, nb = _snap_endpoint(x2, y2, node_list)

            # Update degree counts
            degree[na] = degree.get(na, 0) + 1
            degree[nb] = degree.get(nb, 0) + 1

            length_px = math.hypot(x2 - x1, y2 - y1)
            length_m  = round(length_px * 0.05, 3)

            mx = max(0, min(W-1, int((x1+x2)/2)))
            my = max(0, min(H-1, int((y1+y2)/2)))

            on_perimeter = perimeter_mask[my, mx] > 0
            long_wall    = length_px > W * 0.30

            # Trap 4: load-bearing classification — outer + spine + column proximity
            near_col = _near_column_contour(mx, my, contours, min_area=400, max_area=5000)

            seg = {
                "id":        i,
                "x1": int(x1), "y1": int(y1),
                "x2": int(x2), "y2": int(y2),
                "length_px": round(length_px, 2),
                "length_m":  length_m,
                "angle":     snapped,
                "angle_raw": round(raw_angle, 2),
                "node_a":    na,
                "node_b":    nb,
            }

            if on_perimeter:
                seg["wall_class"] = "load_bearing_outer"
                elements["edges"].append(seg)
            elif near_col:
                seg["wall_class"] = "load_bearing_spine"
                elements["walls"].append(seg)
            elif length_m < 1.2:
                seg["wall_class"] = "opening"
                elements["openings"].append(seg)
            elif long_wall:
                seg["wall_class"] = "load_bearing_spine"
                elements["walls"].append(seg)
            else:
                seg["wall_class"] = "partition"
                elements["walls"].append(seg)

    # Build node list with junction types (Trap 2)
    nodes = [
        {
            "id":     i,
            "x":      int(node_list[i][0]),
            "y":      int(node_list[i][1]),
            "degree": degree.get(i, 0),
            "type":   _classify_junction(i, degree.get(i, 0))
        }
        for i in range(len(node_list))
    ]

    # Contour-based columns and furniture
    col_id = 0; furn_id = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 400: continue
        x, y, w, h = cv2.boundingRect(cnt)
        ar = max(w, h) / (min(w, h) + 1e-5)
        cx, cy = x + w//2, y + h//2

        if 400 <= area <= 5000:
            if ar < 1.5:
                elements["columns"].append({
                    "id": col_id, "type": "column",
                    "x": int(cx), "y": int(cy),
                    "w_m": round(w*0.05,2), "h_m": round(h*0.05,2),
                    "area_px": int(area)
                })
                col_id += 1
            elif ar > 2.5:
                elements["furniture"].append({
                    "id": furn_id, "type": "tv_unit",
                    "x": int(cx), "y": int(cy),
                    "w_m": round(w*0.05,2), "h_m": round(h*0.05,2)
                })
                furn_id += 1
        elif 3000 <= area <= 40000:
            if 1.4 <= ar <= 2.3:
                elements["furniture"].append({
                    "id": furn_id, "type": "bed",
                    "x": int(cx), "y": int(cy),
                    "w_m": round(w*0.05,2), "h_m": round(h*0.05,2)
                })
                furn_id += 1

    # Bounds
    all_pts = []
    for cat in ["edges", "walls", "openings"]:
        for s in elements[cat]:
            all_pts += [(s["x1"], s["y1"]), (s["x2"], s["y2"])]

    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        bounds = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    else:
        bounds = {"min_x": 0, "max_x": W, "min_y": 0, "max_y": H}

    # Junction summary (Trap 2 explainability)
    junc_counts = {"endpoint":0, "corner":0, "t-junction":0, "x-junction":0}
    for n in nodes:
        junc_counts[n["type"]] = junc_counts.get(n["type"], 0) + 1

    summary = {
        "image_size": {"width": W, "height": H},
        "edges":      len(elements["edges"]),
        "walls":      len(elements["walls"]),
        "openings":   len(elements["openings"]),
        "columns":    len(elements["columns"]),
        "furniture":  len(elements["furniture"]),
        "nodes":      len(nodes),
        "junctions":  junc_counts,
        "angle_snaps": sum(1 for cat in ["edges","walls","openings"]
                          for s in elements[cat]
                          if s.get("angle") != s.get("angle_raw")),
    }

    print(f"  Image       : {W}x{H}px")
    print(f"  Outer edges : {summary['edges']}")
    print(f"  Walls       : {summary['walls']}")
    print(f"  Openings    : {summary['openings']}")
    print(f"  Columns     : {summary['columns']}")
    print(f"  Nodes       : {summary['nodes']}  {junc_counts}")
    print(f"  Angle snaps : {summary['angle_snaps']} lines corrected to orthogonal grid")

    return {
        "geometry": {"elements": elements, "bounds": bounds, "nodes": nodes},
        "summary":  summary
    }


def _near_column_contour(mx, my, contours, min_area=400, max_area=5000, radius=40):
    """
    Trap 4 fix: check if a wall midpoint is near a column-like contour.
    Columns near wall midpoints indicate structural spine walls.
    """
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if not (min_area <= area <= max_area):
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        ar = max(w, h) / (min(w, h) + 1e-5)
        if ar >= 1.5:
            continue
        cx, cy = x + w//2, y + h//2
        if math.hypot(mx - cx, my - cy) < radius:
            return True
    return False
