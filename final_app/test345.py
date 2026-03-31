import sys, os, cv2
BASE = os.path.abspath('.')
sys.path.insert(0, os.path.join(BASE, '..', 'try'))
sys.path.insert(0, os.path.join(BASE, '..', 'stage4'))
sys.path.insert(0, os.path.join(BASE, '..', 'stage5'))

# ── Stage 3 ───────────────────────────────────────────────────
print("=== STAGE 3: 3D MODEL ===")
try:
    from vision_parser import parse
    from try_app import build_threejs
    img_path = os.path.join('..', 'sample', 'plan_a.png')
    img = cv2.imread(img_path)
    H, W = img.shape[:2]
    data = parse(img_path)
    os.makedirs('output', exist_ok=True)
    build_threejs(data, W, H, 'output/test_model.html')
    size = os.path.getsize('output/test_model.html')
    print(f"  OK — model saved {size} bytes")
except Exception as e:
    import traceback; traceback.print_exc()

# ── Stage 4 ───────────────────────────────────────────────────
print("\n=== STAGE 4: MATERIALS ===")
try:
    from material_db import load_materials
    from tradeoff_engine import analyze_all
    excel = os.path.join('..', 'stage4', 'Book1.xlsx')
    print(f"  Excel exists: {os.path.exists(excel)}")
    mats = load_materials(excel)
    print(f"  Loaded {len(mats)} materials")
    stats = {'load_bearing_outer':14,'load_bearing_spine':3,'partition':62,'openings':0,'columns':0}
    results = analyze_all(mats, stats)
    for el, recs in results.items():
        print(f"  {el}: #{recs[0]['rank']} {recs[0]['name']} score={recs[0]['tradeoff_score']}")
    print("  OK")
except Exception as e:
    import traceback; traceback.print_exc()

# ── Stage 5 ───────────────────────────────────────────────────
print("\n=== STAGE 5: GEMINI ===")
try:
    from prompt_builder import build_prompt
    import google.genai as genai
    import os
    stage2 = {'summary': stats, 'image_size': {'width': 937, 'height': 669}}
    stage4 = {el: recs for el, recs in results.items()}
    prompt = build_prompt(stage2, stage4)
    print(f"  Prompt: {len(prompt)} chars")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if not GEMINI_API_KEY:
        print("  ERROR: GEMINI_API_KEY environment variable not set")
        raise Exception("API key not found")
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    report = response.text
    print(f"  Report: {len(report)} chars")
    print("-"*50)
    print(report[:800])
    print("-"*50)
    print("  OK")
except Exception as e:
    import traceback; traceback.print_exc()
