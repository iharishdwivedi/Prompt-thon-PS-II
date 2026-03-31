import openpyxl
import os

# Numeric mapping for text values
SCORE_MAP = {
    "low":        1,
    "low-medium":  1.5,
    "medium":     2,
    "medium-high": 2.5,
    "high":       3,
    "very high":  4,
}

def _score(val):
    if val is None:
        return 2
    v = str(val).strip().lower()
    v = v.replace("\u2013", "-").replace("\u2014", "-")
    # handle garbled text like "Low邦edium" → "low-medium"
    for k in SCORE_MAP:
        if k.replace("-","") in v.replace(" ","").replace("-",""):
            return SCORE_MAP[k]
    return SCORE_MAP.get(v, 2)


def load_materials(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    materials = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        name, cost, strength, durability, best_use = row[:5]
        if not name:
            continue
        materials.append({
            "name":       str(name).strip(),
            "cost_raw":   str(cost).strip() if cost else "Medium",
            "strength_raw": str(strength).strip() if strength else "Medium",
            "durability_raw": str(durability).strip() if durability else "Medium",
            "best_use":   str(best_use).strip() if best_use else "",
            "cost":       _score(cost),
            "strength":   _score(strength),
            "durability": _score(durability),
        })

    return materials
