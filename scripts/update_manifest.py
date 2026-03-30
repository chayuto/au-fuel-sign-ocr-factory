#!/usr/bin/env python3
"""Update labeling_manifest.csv from normalized annotation JSONs.

For each annotation file, updates the corresponding manifest row with:
  status=done, has_fuel_sign=yes, brand, sign_type, num_entries, quality=B, labeled_by=normalizer
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ANNOTATIONS_DIR = Path("data/tmp/annotations")
MANIFEST_PATH = Path("data/tmp/labeling_manifest.csv")
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    # Load all annotation data keyed by image filename
    annotations = {}
    for jf in ANNOTATIONS_DIR.glob("*.json"):
        data = json.loads(jf.read_text())
        image_file = data["image"]["file"]
        annotations[image_file] = data

    # Read manifest
    rows = []
    with open(MANIFEST_PATH, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    # Update rows with annotation data
    updated = 0
    for row in rows:
        fname = row["filename"]
        if fname in annotations:
            ann = annotations[fname]
            sign = ann["sign"]
            entries = ann.get("entries", [])
            num_entries = len(entries)

            row["status"] = "done"
            row["has_fuel_sign"] = "yes"
            row["brand"] = sign["brand"]
            row["sign_type"] = sign["sign_type"]
            row["num_entries"] = str(num_entries)
            row["quality"] = "B"  # default — original ratings lost during normalization
            row["labeled_by"] = "normalizer"
            row["timestamp"] = TIMESTAMP
            updated += 1

    # Write manifest back
    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {updated} rows in manifest")
    print(f"Remaining pending: {sum(1 for r in rows if r['status'] == 'pending')}")

    # Auto-generate previews for updated files
    if updated > 0:
        import subprocess
        import sys
        stems = [os.path.splitext(fname)[0] for fname in annotations.keys()]
        script = Path(__file__).parent / "draw_annotations.py"
        if script.exists():
            print(f"\nGenerating {len(stems)} preview images...")
            subprocess.run(
                [sys.executable, str(script), "--files"] + stems,
                capture_output=True,
            )
            print("Previews updated.")


if __name__ == "__main__":
    main()
