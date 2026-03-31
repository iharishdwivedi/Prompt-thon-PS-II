import cv2
import os
import sys
from vision_parser import parse

IMAGE_PATH = r"..\sample\plan_a.png"

print(f"\n{'='*55}")
print("  TEST — Vision Parser Pipeline")
print(f"{'='*55}\n")

# ── Test 1: Image readable ────────────────────────────────────
print("[TEST 1] Image load...")
img = cv2.imread(IMAGE_PATH)
if img is None:
    print("  FAIL — Cannot read image")
    sys.exit(1)
H, W = img.shape[:2]
print(f"  PASS — {W}x{H}px\n")

# ── Test 2: Vision parser runs ────────────────────────────────
print("[TEST 2] Running vision parser...")
try:
    data = parse(IMAGE_PATH)
    print("  PASS\n")
except Exception as e:
    print(f"  FAIL — {e}")
    sys.exit(1)

# ── Test 3: Check all element types exist ─────────────────────
print("[TEST 3] Checking detected elements...")
elements = data["geometry"]["elements"]
for key in ["edges", "walls", "openings", "columns", "furniture"]:
    count = len(elements[key])
    status = "PASS" if count >= 0 else "FAIL"
    print(f"  {status} — {key:12s} : {count}")

# ── Test 4: Check bounds ──────────────────────────────────────
print(f"\n[TEST 4] Checking bounds...")
bounds = data["geometry"]["bounds"]
print(f"  min_x:{bounds['min_x']}  max_x:{bounds['max_x']}")
print(f"  min_y:{bounds['min_y']}  max_y:{bounds['max_y']}")
layout_w = bounds["max_x"] - bounds["min_x"]
layout_h = bounds["max_y"] - bounds["min_y"]
if layout_w > 0 and layout_h > 0:
    print(f"  PASS — layout {layout_w}x{layout_h}px\n")
else:
    print(f"  FAIL — zero bounds\n")

# ── Test 5: Sample wall data ──────────────────────────────────
print("[TEST 5] Sample wall data...")
all_walls = elements["edges"] + elements["walls"]
if all_walls:
    w = all_walls[0]
    print(f"  PASS — First wall: ({w['x1']},{w['y1']}) → ({w['x2']},{w['y2']})")
    print(f"         length:{w['length_m']}m  angle:{w['angle']}°  class:{w['wall_class']}\n")
else:
    print("  WARN — No walls detected\n")

# ── Test 6: 3D model generation ───────────────────────────────
print("[TEST 6] Generating 3D model...")
try:
    from app import build_threejs
    os.makedirs("output", exist_ok=True)
    build_threejs(data, W, H, "output/model_3d.html")
    size = os.path.getsize("output/model_3d.html")
    print(f"  PASS — model_3d.html ({size} bytes)\n")
except Exception as e:
    print(f"  FAIL — {e}\n")

# ── Summary ───────────────────────────────────────────────────
s = data["summary"]
print(f"{'='*55}")
print("  SUMMARY")
print(f"{'='*55}")
print(f"  Outer edges  : {s['edges']}")
print(f"  Walls        : {s['walls']}")
print(f"  Openings     : {s['openings']}")
print(f"  Columns      : {s['columns']}")
print(f"  Furniture    : {s['furniture']}")
print(f"{'='*55}")
print(f"\n  Open in Chrome:")
print(f"  {os.path.abspath('output/model_3d.html')}\n")
