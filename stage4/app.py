import os
import json
from material_db import load_materials
from tradeoff_engine import analyze_all

EXCEL_PATH  = "Book1.xlsx"
STAGE2_JSON = r"..\stage2_3\output\stage2_graph.json"

ELEMENT_LABELS = {
    "load_bearing_outer": "Load-Bearing Outer Walls",
    "load_bearing_spine": "Load-Bearing Spine Walls",
    "partition":          "Partition Walls",
    "slab":               "Floor Slab",
    "column":             "Columns",
}

RANK_ICONS = {1: "🥇", 2: "🥈", 3: "🥉"}


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  STAGE 4 — Material Analysis & Cost-Strength Tradeoff")
    print(f"{'='*60}")

    # ── Load materials from Excel ─────────────────────────────
    if not os.path.exists(EXCEL_PATH):
        print(f"  ERROR: {EXCEL_PATH} not found")
        exit(1)

    materials = load_materials(EXCEL_PATH)
    print(f"\n  Loaded {len(materials)} materials from database")

    # ── Load stage2 wall counts ───────────────────────────────
    if not os.path.exists(STAGE2_JSON):
        print(f"  ERROR: Stage 2 output not found at {STAGE2_JSON}")
        print("  Run stage2_3/app.py first to generate stage2_graph.json")
        exit(1)

    with open(STAGE2_JSON) as f:
        s2 = json.load(f)

    summary = s2.get("summary", {})
    outer_count  = summary.get("load_bearing_outer", 0)
    spine_count  = summary.get("load_bearing_spine", 0)
    part_count   = summary.get("partition", 0)
    room_count   = summary.get("rooms", 0)
    total_walls  = summary.get("edges", 0)

    print(f"\n  Stage 2 detected:")
    print(f"    Load-bearing outer walls : {outer_count}")
    print(f"    Load-bearing spine walls : {spine_count}")
    print(f"    Partition walls          : {part_count}")
    print(f"    Rooms                    : {room_count}")
    print(f"    Total walls              : {total_walls}")

    # ── Only analyze elements that actually exist ─────────────
    active_elements = []
    if outer_count > 0: active_elements.append("load_bearing_outer")
    if spine_count > 0: active_elements.append("load_bearing_spine")
    if part_count  > 0: active_elements.append("partition")
    active_elements.append("slab")    # always needed
    active_elements.append("column")  # always needed

    print(f"\n  Analyzing {len(active_elements)} element types: {', '.join(active_elements)}")

    # ── Run tradeoff analysis ─────────────────────────────────
    results = analyze_all(materials, summary)

    # Filter to only active elements
    results = {k: v for k, v in results.items() if k in active_elements}

    # ── Save JSON ─────────────────────────────────────────────
    out_path = "stage4_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved: {out_path}")

    # ── Print results ─────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  MATERIAL RECOMMENDATIONS")
    print(f"{'='*60}")

    for element, recs in results.items():
        label = ELEMENT_LABELS.get(element, element)
        count = {
            "load_bearing_outer": outer_count,
            "load_bearing_spine": spine_count,
            "partition":          part_count,
            "slab":               room_count,
            "column":             0,
        }.get(element, 0)

        print(f"\n  {'─'*56}")
        print(f"  {label}  ({count} detected)")
        print(f"  {'─'*56}")

        for r in recs:
            icon = RANK_ICONS.get(r["rank"], "  ")
            print(f"\n  {icon}  Rank {r['rank']}: {r['name']}")
            print(f"       Cost       : {r['cost_raw']}")
            print(f"       Strength   : {r['strength_raw']}")
            print(f"       Durability : {r['durability_raw']}")
            print(f"       Best use   : {r['best_use']}")
            print(f"       Score      : {r['tradeoff_score']}")

    print(f"\n{'='*60}\n")
