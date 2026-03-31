import cv2
import json
import os
from parser.ocr_detector import extract_text, count_rooms


def parse_floorplan(image_path, output_dir="output"):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    texts       = extract_text(img)
    room_counts = count_rooms(texts)

    dimensions  = [t for t in texts if t["category"] == "dimension"]
    room_labels = [t for t in texts if t["category"] == "room_label"]
    annotations = [t for t in texts if t["category"] == "annotation"]

    result = {
        "image": image_path,
        "room_counts": room_counts,
        "ocr": {
            "dimensions":  dimensions,
            "room_labels": room_labels,
            "annotations": annotations,
        }
    }

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(image_path))[0]
    json_path = os.path.join(output_dir, f"{base}_ocr.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    rc = result["room_counts"]
    print(f"\nROOM COUNT RESULTS")
    print(f"{'='*55}")
    print(f"  Bedrooms  : {rc.get('bedroom', 0)}")
    print(f"  Bathrooms : {rc.get('bathroom', 0)}")
    print(f"{'='*55}\n")

    return result
