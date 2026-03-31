import json
import os
from image_processor import process_image
from graph_builder import build_graph, classify_walls
from threejs_exporter import export_threejs

# ── Set your image path here ──
IMAGE_PATH = r"..\sample\plan_a.png"
OUTPUT_DIR = "output"
# ─────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*55}")
    print("  STAGE 2+3 — Geometry Reconstruction + 3D Generation")
    print(f"{'='*55}")

    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found: {IMAGE_PATH}")
        exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Stage 2: Image processing ────────────────────────────────
    print("\n[1/3] Processing image (grayscale → binary → Hough)...")
    data = process_image(IMAGE_PATH)

    # ── Stage 2: Graph + classification ─────────────────────────
    print("\n[2/3] Building graph and classifying walls...")
    nodes, edges = build_graph(data["segments"])
    classified   = classify_walls(nodes, edges, data["image_size"]["width"], data["image_size"]["height"])

    outer  = [e for e in classified if e["wall_class"] == "load_bearing_outer"]
    spine  = [e for e in classified if e["wall_class"] == "load_bearing_spine"]
    parts  = [e for e in classified if e["wall_class"] == "partition"]

    print(f"  Nodes                : {len(nodes)}")
    print(f"  Edges                : {len(edges)}")
    print(f"  Load-bearing outer   : {len(outer)}")
    print(f"  Load-bearing spine   : {len(spine)}")
    print(f"  Partition walls      : {len(parts)}")
    print(f"  Rooms                : {len(data['rooms'])}")

    # ── Save stage2 JSON ─────────────────────────────────────────
    stage2_json = os.path.join(OUTPUT_DIR, "stage2_graph.json")
    with open(stage2_json, "w") as f:
        json.dump({
            "image_size": data["image_size"],
            "nodes": nodes,
            "walls": classified,
            "rooms": data["rooms"],
            "summary": {
                "nodes": len(nodes),
                "edges": len(edges),
                "load_bearing_outer": len(outer),
                "load_bearing_spine": len(spine),
                "partition": len(parts),
                "rooms": len(data["rooms"])
            }
        }, f, indent=2)
    print(f"\n  Stage 2 JSON saved: {stage2_json}")

    # ── Stage 3: Three.js 3D export ──────────────────────────────
    print("\n[3/3] Generating 3D model (Three.js)...")
    html_path = os.path.join(OUTPUT_DIR, "model_3d.html")
    export_threejs(
        classified_edges=classified,
        rooms=data["rooms"],
        image_w=data["image_size"]["width"],
        image_h=data["image_size"]["height"],
        output_path=html_path
    )

    print(f"\n{'='*55}")
    print("  DONE")
    print(f"{'='*55}")
    print(f"  Stage 2 JSON : {stage2_json}")
    print(f"  3D Viewer    : {html_path}")
    print(f"\n  Open the 3D viewer in your browser:")
    print(f"  {os.path.abspath(html_path)}")
    print(f"{'='*55}\n")
