import cv2
import numpy as np
import os


def process_image(image_path):
    """
    Full image processing pipeline:
    1. Grayscale conversion
    2. Binary thresholding (Otsu)
    3. Morphological cleanup
    4. Hough line detection for walls
    Returns processed data needed for graph building.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {image_path}")

    h, w = img.shape[:2]

    # ── Step 1: Grayscale ────────────────────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ── Step 2: Binary (Otsu auto-threshold) ────────────────────
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # ── Step 3: Morphological cleanup ───────────────────────────
    kernel = np.ones((3, 3), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN,  kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

    # ── Step 4: Hough line detection ────────────────────────────
    edges = cv2.Canny(cleaned, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=60,
        minLineLength=30,
        maxLineGap=8
    )

    segments = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = float(np.hypot(x2 - x1, y2 - y1))
            angle  = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            segments.append({
                "x1": int(x1), "y1": int(y1),
                "x2": int(x2), "y2": int(y2),
                "length": round(length, 2),
                "angle":  round(angle, 2)
            })

    # ── Step 5: Room detection via connected components ─────────
    wall_thick = np.ones((7, 7), np.uint8)
    dilated    = cv2.dilate(cleaned, wall_thick, iterations=3)
    inverted   = cv2.bitwise_not(dilated)
    border     = np.zeros_like(inverted)
    cv2.rectangle(border, (5, 5), (w - 5, h - 5), 255, -1)
    inverted   = cv2.bitwise_and(inverted, border)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inverted, connectivity=8)

    rooms = []
    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < 4000:
            continue
        rx  = int(stats[i, cv2.CC_STAT_LEFT])
        ry  = int(stats[i, cv2.CC_STAT_TOP])
        rw  = int(stats[i, cv2.CC_STAT_WIDTH])
        rh  = int(stats[i, cv2.CC_STAT_HEIGHT])
        cx  = float(centroids[i][0])
        cy  = float(centroids[i][1])
        rooms.append({
            "id": i,
            "bbox": {"x": rx, "y": ry, "w": rw, "h": rh},
            "area_px": area,
            "centroid": {"x": round(cx, 1), "y": round(cy, 1)}
        })

    print(f"  Image size     : {w}x{h} px")
    print(f"  Wall segments  : {len(segments)}")
    print(f"  Rooms detected : {len(rooms)}")

    # ── Save debug images ────────────────────────────────────────
    debug_dir = "output"
    os.makedirs(debug_dir, exist_ok=True)

    # 1. Grayscale
    cv2.imwrite(os.path.join(debug_dir, "debug_1_grayscale.png"), gray)

    # 2. Binary
    cv2.imwrite(os.path.join(debug_dir, "debug_2_binary.png"), cleaned)

    # 3. Hough lines on original
    hough_vis = img.copy()
    for seg in segments:
        cv2.line(hough_vis, (seg["x1"], seg["y1"]), (seg["x2"], seg["y2"]), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(debug_dir, "debug_3_hough_lines.png"), hough_vis)

    # 4. Rooms on original
    room_vis = img.copy()
    for r in rooms:
        b = r["bbox"]
        overlay = room_vis.copy()
        cv2.rectangle(overlay, (b["x"], b["y"]), (b["x"]+b["w"], b["y"]+b["h"]), (0, 180, 0), -1)
        cv2.addWeighted(overlay, 0.25, room_vis, 0.75, 0, room_vis)
        cv2.rectangle(room_vis, (b["x"], b["y"]), (b["x"]+b["w"], b["y"]+b["h"]), (0, 220, 0), 2)
        cx2 = b["x"] + b["w"]//2
        cy2 = b["y"] + b["h"]//2
        cv2.putText(room_vis, "R"+str(r["id"]), (cx2-10, cy2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.imwrite(os.path.join(debug_dir, "debug_4_rooms.png"), room_vis)

    # 5. Full combined
    full_vis = img.copy()
    for seg in segments:
        cv2.line(full_vis, (seg["x1"], seg["y1"]), (seg["x2"], seg["y2"]), (0, 255, 0), 1)
    for r in rooms:
        b = r["bbox"]
        cv2.rectangle(full_vis, (b["x"], b["y"]), (b["x"]+b["w"], b["y"]+b["h"]), (0, 200, 255), 2)
    cv2.imwrite(os.path.join(debug_dir, "debug_5_combined.png"), full_vis)

    print(f"  Debug images saved to output/")
    print(f"    debug_1_grayscale.png")
    print(f"    debug_2_binary.png")
    print(f"    debug_3_hough_lines.png")
    print(f"    debug_4_rooms.png")
    print(f"    debug_5_combined.png")

    return {
        "image_size": {"width": w, "height": h},
        "segments":   segments,
        "rooms":      rooms,
        "gray":       gray,
        "binary":     cleaned
    }
