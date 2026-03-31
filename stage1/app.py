import os
from parser.floorplan_parser import parse_floorplan

# ── Set your image path here ──
IMAGE_PATH = r"..\sample\plan_a.png"
# ─────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found: {IMAGE_PATH}")
    else:
        parse_floorplan(IMAGE_PATH, "output")
