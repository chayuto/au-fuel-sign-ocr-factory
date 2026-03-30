#!/usr/bin/env python3
"""Normalize all JSON annotation files to the canonical FuelSignAnnotation schema.

Handles 5 schema variants produced by different labeling agents:
  Type 1: Canonical nested (image/sign/entries) - already correct
  Type 2: Multi-sign (signs[] array) - picks largest sign
  Type 3: Flat with bboxes dict (filename, bboxes: {sign_board: [[...]]})
  Type 4: Flat with bboxes list + bbox_norm (bboxes: [{class_id, bbox_norm}])
  Type 5: Flat with boxes list + bbox (boxes: [{class_id, bbox}])

Also:
  - Drops entries with null label_bbox (unpaired prices)
  - Fills missing sign_type with "led" default
  - Regenerates YOLO .txt label files from normalized JSON
  - Reports all changes made
"""

import json
import sys
from pathlib import Path

ANNOTATIONS_DIR = Path("data/tmp/annotations")
LABELS_DIR = Path("data/tmp/labels")


def detect_schema_type(data: dict) -> str:
    if "signs" in data:
        return "multi_sign"
    if "image" in data and "sign" in data:
        return "canonical"
    if "boxes" in data:
        return "boxes_list"
    if "bboxes" in data and isinstance(data["bboxes"], list):
        return "bboxes_list_norm"
    if "bboxes" in data and isinstance(data["bboxes"], dict):
        return "bboxes_dict"
    raise ValueError(f"Unknown schema: keys={list(data.keys())}")


def bbox_area(bbox: list[float]) -> float:
    """Area of [x1, y1, x2, y2] bbox."""
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def normalize_canonical(data: dict) -> dict:
    """Type 1: Already canonical. Just ensure all fields present."""
    sign = data["sign"]
    if "sign_type" not in sign:
        sign["sign_type"] = "led"
    # Remove null brand_bbox (some agents wrote null instead of omitting)
    if sign.get("brand_bbox") is None and "brand_bbox" in sign:
        del sign["brand_bbox"]
    return data


def normalize_multi_sign(data: dict) -> dict:
    """Type 2: Pick the largest sign from signs[] array."""
    signs = data["signs"]
    largest = max(signs, key=lambda s: bbox_area(s["bbox"]))

    return {
        "image": {
            "file": data["image"]["file"],
            "source": data["image"].get("source", "web"),
            "conditions": data["image"].get("conditions", {"time_of_day": "day", "weather": "clear"}),
        },
        "sign": {
            "bbox": largest["bbox"],
            "brand": largest["brand"],
            "sign_type": largest.get("sign_type", "led"),
            **({"brand_bbox": largest["brand_bbox"]} if "brand_bbox" in largest else {}),
        },
        "entries": largest.get("entries", []),
    }


def normalize_bboxes_dict(data: dict) -> dict:
    """Type 3: Flat format with bboxes as dict of class arrays."""
    bboxes = data["bboxes"]
    sign_bbox = bboxes.get("sign_board", [[]])[0] if bboxes.get("sign_board") else [0, 0, 1, 1]
    brand_bbox = bboxes.get("brand_zone", [[]])[0] if bboxes.get("brand_zone") else None

    # Build entries from the entries array, filtering out null label_bbox
    entries = []
    for e in data.get("entries", []):
        label_bbox = e.get("label_bbox")
        price_bbox = e.get("price_bbox")
        if label_bbox is None or price_bbox is None:
            continue
        price_val = e.get("price")
        if isinstance(price_val, str):
            try:
                price_val = float(price_val)
            except ValueError:
                continue
        entries.append({
            "fuel_type": e.get("fuel_type", "U91"),
            "display_text": e.get("label_text") or e.get("display_text", ""),
            "price": price_val,
            "label_bbox": label_bbox,
            "price_bbox": price_bbox,
        })

    result = {
        "image": {
            "file": data["filename"],
            "source": "web",
            "conditions": data.get("conditions", {"time_of_day": "day", "weather": "clear"}),
        },
        "sign": {
            "bbox": sign_bbox,
            "brand": data.get("brand", "independent"),
            "sign_type": data.get("sign_type", "led"),
        },
        "entries": entries,
    }
    if brand_bbox:
        result["sign"]["brand_bbox"] = brand_bbox
    return result


def normalize_bboxes_list_norm(data: dict) -> dict:
    """Type 4: bboxes as list of {class_id, bbox_norm, ...}."""
    bboxes = data["bboxes"]

    sign_bbox = [0, 0, 1, 1]
    brand_bbox = None
    label_items = []
    price_items = []

    for b in bboxes:
        cls = b["class_id"]
        bbox = b["bbox_norm"]
        if cls == 0:
            sign_bbox = bbox
        elif cls == 1:
            brand_bbox = bbox
        elif cls == 2:
            label_items.append(b)
        elif cls == 3:
            price_items.append(b)

    # Pair labels and prices by Y-coordinate proximity
    entries = _pair_labels_prices(label_items, price_items, bbox_key="bbox_norm")

    result = {
        "image": {
            "file": data["filename"],
            "source": "web",
            "conditions": data.get("conditions", {"time_of_day": "day", "weather": "clear"}),
        },
        "sign": {
            "bbox": sign_bbox,
            "brand": data.get("brand", "independent"),
            "sign_type": data.get("sign_type", "led"),
        },
        "entries": entries,
    }
    if brand_bbox:
        result["sign"]["brand_bbox"] = brand_bbox
    return result


def normalize_boxes_list(data: dict) -> dict:
    """Type 5: boxes as list of {class_id, bbox, ...}."""
    boxes = data["boxes"]

    sign_bbox = [0, 0, 1, 1]
    brand_bbox = None
    label_items = []
    price_items = []

    for b in boxes:
        cls = b["class_id"]
        bbox = b["bbox"]
        if cls == 0:
            sign_bbox = bbox
        elif cls == 1:
            brand_bbox = bbox
        elif cls == 2:
            label_items.append(b)
        elif cls == 3:
            price_items.append(b)

    entries = _pair_labels_prices(label_items, price_items, bbox_key="bbox")

    result = {
        "image": {
            "file": data["filename"],
            "source": "web",
            "conditions": data.get("conditions", {"time_of_day": "day", "weather": "clear"}),
        },
        "sign": {
            "bbox": sign_bbox,
            "brand": data.get("brand", "independent"),
            "sign_type": data.get("sign_type", "led"),
        },
        "entries": entries,
    }
    if brand_bbox:
        result["sign"]["brand_bbox"] = brand_bbox
    return result


def _pair_labels_prices(labels: list, prices: list, bbox_key: str) -> list[dict]:
    """Pair label and price items by Y-coordinate proximity (greedy matching)."""
    entries = []
    used_prices = set()

    for lbl in labels:
        lbl_bbox = lbl[bbox_key]
        lbl_cy = (lbl_bbox[1] + lbl_bbox[3]) / 2
        best_price = None
        best_dist = float("inf")

        for i, pr in enumerate(prices):
            if i in used_prices:
                continue
            pr_bbox = pr[bbox_key]
            pr_cy = (pr_bbox[1] + pr_bbox[3]) / 2
            dist = abs(lbl_cy - pr_cy)
            if dist < best_dist:
                best_dist = dist
                best_price = (i, pr)

        if best_price is None or best_dist > 0.1:
            continue

        idx, pr = best_price
        used_prices.add(idx)

        price_val = pr.get("price", 0.0)
        if isinstance(price_val, str):
            try:
                price_val = float(price_val)
            except ValueError:
                price_val = 0.0

        entries.append({
            "fuel_type": lbl.get("fuel_type", "U91"),
            "display_text": lbl.get("display_text", ""),
            "price": price_val,
            "label_bbox": lbl[bbox_key],
            "price_bbox": pr[bbox_key],
        })

    return entries


def to_yolo_lines(data: dict) -> list[str]:
    """Convert canonical JSON to YOLO label lines."""
    lines = []
    sign = data["sign"]

    # Class 0: sign_board
    bbox = sign["bbox"]
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    lines.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # Class 1: brand_zone
    if "brand_bbox" in sign:
        bbox = sign["brand_bbox"]
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        lines.append(f"1 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # Classes 2+3: fuel_label + fuel_price pairs
    for entry in data.get("entries", []):
        bbox = entry["label_bbox"]
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        lines.append(f"2 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        bbox = entry["price_bbox"]
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        lines.append(f"3 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    return lines


def main():
    changes = []
    errors = []

    json_files = sorted(ANNOTATIONS_DIR.glob("*.json"))
    print(f"Found {len(json_files)} annotation files\n")

    for jf in json_files:
        stem = jf.stem
        try:
            data = json.loads(jf.read_text())
            schema_type = detect_schema_type(data)

            if schema_type == "canonical":
                normalized = normalize_canonical(data)
            elif schema_type == "multi_sign":
                normalized = normalize_multi_sign(data)
            elif schema_type == "bboxes_dict":
                normalized = normalize_bboxes_dict(data)
            elif schema_type == "bboxes_list_norm":
                normalized = normalize_bboxes_list_norm(data)
            elif schema_type == "boxes_list":
                normalized = normalize_boxes_list(data)
            else:
                errors.append(f"{stem}: unknown schema type")
                continue

            # Write normalized JSON
            jf.write_text(json.dumps(normalized, indent=2) + "\n")

            # Generate YOLO labels
            yolo_lines = to_yolo_lines(normalized)
            label_file = LABELS_DIR / f"{stem}.txt"
            label_file.write_text("\n".join(yolo_lines) + "\n")

            n_entries = len(normalized.get("entries", []))
            brand = normalized["sign"]["brand"]
            sign_type = normalized["sign"]["sign_type"]
            has_brand_bbox = "brand_bbox" in normalized["sign"]

            changes.append({
                "file": stem,
                "type": schema_type,
                "brand": brand,
                "sign_type": sign_type,
                "entries": n_entries,
                "brand_bbox": has_brand_bbox,
                "yolo_lines": len(yolo_lines),
            })

        except Exception as e:
            errors.append(f"{stem}: {e}")

    # Summary
    print("=" * 70)
    print("NORMALIZATION RESULTS")
    print("=" * 70)

    type_counts = {}
    for c in changes:
        t = c["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\nSchema types found:")
    for t, count in sorted(type_counts.items()):
        print(f"  {t}: {count}")

    print(f"\nTotal files normalized: {len(changes)}")
    print(f"Total errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")

    # Per-file summary
    print(f"\n{'File':<55} {'Type':<18} {'Brand':<12} {'Entries':>7} {'YOLO':>5}")
    print("-" * 100)
    for c in changes:
        print(f"{c['file']:<55} {c['type']:<18} {c['brand']:<12} {c['entries']:>7} {c['yolo_lines']:>5}")

    # Warnings
    zero_entries = [c for c in changes if c["entries"] == 0]
    if zero_entries:
        print(f"\n⚠ {len(zero_entries)} files with 0 entries (sign_board/brand_zone only):")
        for c in zero_entries:
            print(f"  {c['file']}")

    # Auto-generate previews for all normalized files
    stems = [c["file"] for c in changes]
    _generate_previews(stems)


def _generate_previews(stems: list[str]):
    """Run draw_annotations.py on the given stems to generate visual QA previews."""
    import subprocess
    script = Path(__file__).parent / "draw_annotations.py"
    if not script.exists():
        print("\n⚠ draw_annotations.py not found — skipping preview generation")
        return

    print(f"\nGenerating {len(stems)} preview images...")
    result = subprocess.run(
        [sys.executable, str(script), "--files"] + stems,
        capture_output=True, text=True,
    )
    # Print only the issues summary, not per-file output
    for line in result.stdout.split("\n"):
        if "issues" in line.lower() or line.startswith("  ") and ":" in line or "=" in line:
            print(line)
    if result.returncode != 0 and result.stderr:
        print(f"Preview generation warnings: {result.stderr[:200]}")


if __name__ == "__main__":
    main()
