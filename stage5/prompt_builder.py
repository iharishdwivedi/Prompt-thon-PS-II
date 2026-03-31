"""
Builds a structured prompt for Gemini from stage2 graph + stage4 material results.
The prompt is designed to get specific, property-citing explanations — not generic ones.
"""

ELEMENT_LABELS = {
    "load_bearing_outer": "Load-Bearing Outer Walls",
    "load_bearing_spine": "Load-Bearing Spine Walls",
    "partition":          "Partition Walls",
    "slab":               "Floor Slab",
    "column":             "Columns",
}


def build_prompt(stage2_data: dict, stage4_data: dict) -> str:
    s2 = stage2_data.get("summary", {})
    iw = stage2_data.get("image_size", {}).get("width", 0)
    ih = stage2_data.get("image_size", {}).get("height", 0)

    outer  = s2.get("load_bearing_outer", 0)
    spine  = s2.get("load_bearing_spine", 0)
    parts  = s2.get("partition", 0)
    rooms  = s2.get("rooms", 0)
    # support both key names from different pipeline versions
    nodes  = s2.get("nodes", s2.get("graph_nodes", 0))
    edges  = s2.get("wall_segments", s2.get("edges", outer + spine + parts))

    floor_w = round(iw * 0.05, 1)
    floor_h = round(ih * 0.05, 1)

    # Build material section
    mat_lines = []
    for element, recs in stage4_data.items():
        label = ELEMENT_LABELS.get(element, element)
        mat_lines.append(f"\n{label}:")
        for r in recs:
            mat_lines.append(
                f"  Rank {r['rank']}: {r['name']} | "
                f"Cost={r['cost_raw']} | Strength={r['strength_raw']} | "
                f"Durability={r['durability_raw']} | "
                f"Tradeoff Score={r['tradeoff_score']} | "
                f"Best use: {r['best_use']}"
            )

    mat_section = "\n".join(mat_lines)

    prompt = f"""You are a structural engineering AI assistant analyzing a floor plan.

FLOOR PLAN DATA (from computer vision analysis):
- Floor plan dimensions: {floor_w}m x {floor_h}m
- Total wall segments detected: {edges}
- Load-bearing outer walls: {outer}
- Load-bearing spine walls: {spine}
- Partition walls: {parts}
- Rooms detected: {rooms}
- Graph nodes (junctions): {nodes}

MATERIAL RECOMMENDATIONS (from cost-strength tradeoff analysis):
{mat_section}

WEIGHT RATIONALE USED:
- Load-bearing outer: strength=0.55, durability=0.15, cost=0.30 (strength dominates — outer walls carry vertical + lateral loads)
- Load-bearing spine: strength=0.50, durability=0.25, cost=0.25 (strength + durability balanced — spine carries floor loads across spans)
- Partition: cost=0.60, strength=0.20, durability=0.20 (cost dominates — partitions are non-structural)
- Slab: strength=0.40, durability=0.35, cost=0.25 (durability critical — slabs face cyclic loading + moisture)
- Column: strength=0.65, durability=0.20, cost=0.15 (strength is everything — column failure cascades to floor collapse)

YOUR TASK:
Write a clear, plain-language structural analysis report with the following sections:

1. FLOOR PLAN OVERVIEW
   Describe the building's structural layout based on the detected data. Mention the floor dimensions, number of structural walls, and what the junction count tells us about the complexity of the layout.

2. MATERIAL RECOMMENDATIONS — WHY EACH WAS CHOSEN
   For each structural element (outer walls, spine walls, partitions, slab, columns):
   - Name the top recommended material
   - Explain WHY it was chosen — cite its specific strength, cost, and durability values
   - Explain what would happen if a cheaper or weaker material was used instead
   - Mention the weight rationale (why strength/cost/durability was weighted as it was for this element)

3. COST-STRENGTH TRADEOFF ANALYSIS
   - Compare the top 2 options for the most critical element (load-bearing outer walls)
   - Explain the tradeoff score formula: score = (w_strength × strength + w_durability × durability) / (w_cost × cost)
   - Show with actual numbers why Rank 1 scored higher than Rank 2

4. STRUCTURAL CONCERNS
   Based on the detected data, flag any concerns:
   - Are there large unsupported spans? (floor is {floor_w}m x {floor_h}m with only {spine} spine walls)
   - Is the partition-to-load-bearing ratio healthy? ({parts} partitions vs {outer + spine} load-bearing)
   - Any junction complexity concerns? ({nodes} nodes detected)
   - Recommend if any additional structural elements (columns, beams) should be considered

5. SUMMARY
   One paragraph plain-language summary a non-engineer client could understand.

Be specific. Cite actual numbers. Do not give generic advice. Every claim must reference the data above.
"""
    return prompt
