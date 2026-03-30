#!/usr/bin/env python3
"""Extract fuel type label crops from annotated images for classifier training.

For each annotated image, extracts the left-of-price region for each fuel entry
and saves it as a labeled crop for the Fuel Type Classifier.

Output structure:
    data/classifier/fuel_type/
        U91/   E10/   P95/   P98/   Diesel/   LPG/   AdBlue/   E85/
        Each contains cropped label images.

Also generates a train/val split manifest.
"""

import csv
import json
import os
import random
from pathlib import Path

import cv2

SRC_DIR = Path("data/tmp")
DST_DIR = Path("data/classifier/fuel_type")
MANIFEST = SRC_DIR / "labeling_manifest.csv"
SEED = 42
VAL_RATIO = 0.15


def main():
    random.seed(SEED)

    # Load all labeled images
    labeled = []
    with open(MANIFEST) as f:
        for row in csv.DictReader(f):
            if row["status"] != "done":
                continue
            fname = row["filename"]
            stem = os.path.splitext(fname)[0]
            ann_path = SRC_DIR / "annotations" / f"{stem}.json"
            img_path = SRC_DIR / fname
            if ann_path.exists() and img_path.exists():
                labeled.append((img_path, ann_path))

    print(f"Found {len(labeled)} labeled images")

    # Extract crops
    crops_by_type = {}
    total = 0
    skipped = 0

    for img_path, ann_path in labeled:
        data = json.loads(ann_path.read_text())
        sign = data["sign"]
        entries = data.get("entries", [])
        sign_x1 = sign["bbox"][0]

        image = cv2.imread(str(img_path))
        if image is None:
            continue
        h, w = image.shape[:2]

        for entry in entries:
            fuel_type = entry["fuel_type"]
            price_bbox = entry["price_bbox"]

            # Derive label region: sign left edge → price left edge, same Y band
            label_x1 = max(0, int(sign_x1 * w))
            label_y1 = max(0, int(price_bbox[1] * h) - 2)
            label_x2 = max(0, int(price_bbox[0] * w))
            label_y2 = min(h, int(price_bbox[3] * h) + 2)

            if label_x2 <= label_x1 + 4 or label_y2 <= label_y1 + 4:
                skipped += 1
                continue

            crop = image[label_y1:label_y2, label_x1:label_x2]
            if crop.size == 0:
                skipped += 1
                continue

            if fuel_type not in crops_by_type:
                crops_by_type[fuel_type] = []
            crops_by_type[fuel_type].append(crop)
            total += 1

    print(f"Extracted {total} crops, skipped {skipped}")
    print(f"Distribution:")
    for ft in sorted(crops_by_type.keys()):
        print(f"  {ft}: {len(crops_by_type[ft])}")

    # Save crops with train/val split
    train_manifest = []
    val_manifest = []

    for fuel_type, crops in crops_by_type.items():
        random.shuffle(crops)
        n_val = max(1, int(len(crops) * VAL_RATIO))

        for split, items in [("train", crops[n_val:]), ("val", crops[:n_val])]:
            split_dir = DST_DIR / split / fuel_type
            split_dir.mkdir(parents=True, exist_ok=True)

            for i, crop in enumerate(items):
                fname = f"{fuel_type}_{i:04d}.jpg"
                fpath = split_dir / fname
                cv2.imwrite(str(fpath), crop)

                entry = {"path": str(fpath), "fuel_type": fuel_type}
                if split == "train":
                    train_manifest.append(entry)
                else:
                    val_manifest.append(entry)

    print(f"\nSaved to {DST_DIR}")
    print(f"  Train: {len(train_manifest)} crops")
    print(f"  Val:   {len(val_manifest)} crops")

    # Save manifest
    for name, items in [("train", train_manifest), ("val", val_manifest)]:
        manifest_path = DST_DIR / f"{name}.csv"
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "fuel_type"])
            writer.writeheader()
            writer.writerows(items)


if __name__ == "__main__":
    main()
