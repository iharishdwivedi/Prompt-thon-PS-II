import easyocr
import cv2
import re
from collections import Counter

_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        print("  Loading EasyOCR model (first run downloads ~100MB)...")
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader


def _normalize_room(text):
    t = text.upper().strip()
    if re.search(r'\bBED\b|BEDROOM|BED\s*ROOM', t):
        return "bedroom"
    if re.search(r'\bBATH\b|BATHROOM|BATH\s*ROOM|BATHRM', t):
        return "bathroom"
    if re.search(r'\bWC\b|TOILET|RESTROOM', t):
        return "toilet"
    if re.search(r'KITCHEN|KITCH|\bKIT\b', t):
        return "kitchen"
    if re.search(r'LIVING|LOUNGE|SITTING', t):
        return "living_room"
    if re.search(r'DINING|DINE', t):
        return "dining"
    if re.search(r'HALL|CORRIDOR|LOBBY|PASSAGE', t):
        return "hall"
    if re.search(r'BALCONY|TERRACE', t):
        return "balcony"
    if re.search(r'STORE|STORAGE|UTILITY|PANTRY', t):
        return "store"
    if re.search(r'GARAGE', t):
        return "garage"
    if re.search(r'STAIR|LIFT|ELEVATOR', t):
        return "stair"
    if re.search(r'STUDY|OFFICE', t):
        return "study"
    return None


def _categorize(text):
    t = text.upper().strip()
    if re.match(r'^\d+(\.\d+)?\s*(mm|m|cm|ft|\'|\")?$', t):
        return "dimension"
    if _normalize_room(text) is not None:
        return "room_label"
    return "annotation"


def extract_text(img):
    reader = _get_reader()

    h, w = img.shape[:2]
    scale = 1.0
    if w < 1000:
        scale = 1000 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    results = reader.readtext(img)

    texts = []
    for (bbox, text, conf) in results:
        if conf < 0.2:
            continue
        text = text.strip()
        if not text:
            continue

        pts = [[int(p[0] / scale), int(p[1] / scale)] for p in bbox]
        cx = int(sum(p[0] for p in pts) / 4)
        cy = int(sum(p[1] for p in pts) / 4)
        category = _categorize(text)
        normalized = _normalize_room(text) if category == "room_label" else None

        texts.append({
            "text":       text,
            "confidence": round(float(conf), 3),
            "bbox_pts":   pts,
            "centroid":   {"x": cx, "y": cy},
            "category":   category,
            "normalized": normalized
        })

    return texts


def count_rooms(texts):
    """Count occurrences of each normalized room type."""
    counts = Counter()
    for t in texts:
        if t["normalized"]:
            counts[t["normalized"]] += 1
    return dict(counts)
