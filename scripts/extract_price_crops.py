#!/usr/bin/env python3
"""Extract price crops from annotated images for Reader training.

Reads annotations from data/tmp/annotations/*.json, crops each price_bbox
region from the source image, and saves to data/reader_experts/price/.

Output structure:
    data/reader_experts/price/
        crops/          # {stem}_{entry_idx}.jpg  (grayscale, height=48)
        labels.csv      # filename,price_text
        train/          # after split
        val/

Usage:
    .venv/bin/python scripts/extract_price_crops.py [--val-pct 0.15] [--seed 42]
"""

import argparse
import csv
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np


IMG_HEIGHT = 48
SRC_DIR = Path("data/tmp")
ANN_DIR = SRC_DIR / "annotations"
OUT_DIR = Path("data/reader_experts/price")


def crop_bbox(img: np.ndarray, bbox: list[float], normalized: bool = True) -> np.ndarray:
    """Crop a bounding box from an image.

    bbox: [x1, y1, x2, y2] in normalized [0,1] or pixel coordinates.
    """
    h, w = img.shape[:2]
    if normalized:
        x1 = int(bbox[0] * w)
        y1 = int(bbox[1] * h)
        x2 = int(bbox[2] * w)
        y2 = int(bbox[3] * h)
    else:
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

    # Clamp to image bounds
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))

    return img[y1:y2, x1:x2]


def format_price(price: float) -> str:
    """Format price as XXX.X string (one decimal place)."""
    return f"{price:.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val-pct", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    crops_dir = OUT_DIR / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)

    all_crops = []  # (filename, price_text)
    skipped = {"no_image": 0, "too_small": 0, "bad_price": 0}

    annotations = sorted(ANN_DIR.glob("*.json"))
    print(f"Found {len(annotations)} annotations")

    for ann_path in annotations:
        data = json.loads(ann_path.read_text())
        stem = ann_path.stem

        # Find source image
        img_field = data.get("image", data.get("image_file", ""))
        if isinstance(img_field, dict):
            img_file = img_field.get("file", "")
        else:
            img_file = img_field
        if img_file:
            img_path = SRC_DIR / img_file
        else:
            img_path = SRC_DIR / f"{stem}.jpg"
            if not img_path.exists():
                img_path = SRC_DIR / f"{stem}.png"

        if not img_path.exists():
            skipped["no_image"] += 1
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            skipped["no_image"] += 1
            continue

        ih, iw = img.shape[:2]

        # Detect coordinate format
        entries = data.get("entries", [])
        is_pixel = any(
            max(e.get("price_bbox", [0])) > 1.0
            for e in entries
            if "price_bbox" in e
        )

        for idx, entry in enumerate(entries):
            price_bbox = entry.get("price_bbox")
            price_val = entry.get("price")
            if not price_bbox or price_val is None:
                continue

            # Validate price
            try:
                price_float = float(price_val)
            except (ValueError, TypeError):
                skipped["bad_price"] += 1
                continue

            if price_float < 10.0 or price_float > 400.0:
                skipped["bad_price"] += 1
                continue

            # Crop
            crop = crop_bbox(img, price_bbox, normalized=not is_pixel)
            ch, cw = crop.shape[:2]

            if ch < 5 or cw < 5:
                skipped["too_small"] += 1
                continue

            # Resize to fixed height, preserve aspect ratio
            new_w = max(1, int(cw * IMG_HEIGHT / ch))
            crop_resized = cv2.resize(crop, (new_w, IMG_HEIGHT))

            # Convert to grayscale
            if len(crop_resized.shape) == 3:
                crop_gray = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2GRAY)
            else:
                crop_gray = crop_resized

            # Save
            price_text = format_price(price_float)
            crop_name = f"{stem}_{idx}.jpg"
            cv2.imwrite(str(crops_dir / crop_name), crop_gray)
            all_crops.append((crop_name, price_text))

    print(f"\nExtracted {len(all_crops)} price crops")
    print(f"Skipped: {skipped}")

    # Write labels.csv
    with open(OUT_DIR / "labels.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label"])
        for name, label in sorted(all_crops):
            writer.writerow([name, label])

    # Train/val split
    random.seed(args.seed)
    random.shuffle(all_crops)
    n_val = int(len(all_crops) * args.val_pct)
    val_crops = all_crops[:n_val]
    train_crops = all_crops[n_val:]

    for split_name, split_crops in [("train", train_crops), ("val", val_crops)]:
        split_dir = OUT_DIR / split_name
        if split_dir.exists():
            shutil.rmtree(split_dir)
        split_dir.mkdir(parents=True)

        with open(split_dir / "labels.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "label"])
            for name, label in split_crops:
                shutil.copy2(crops_dir / name, split_dir / name)
                writer.writerow([name, label])

    print(f"\nSplit: {len(train_crops)} train, {len(val_crops)} val")

    # Price distribution summary
    prices = [float(label) for _, label in all_crops]
    print(f"\nPrice range: {min(prices):.1f} - {max(prices):.1f}")
    print(f"Unique prices: {len(set(format_price(p) for p in prices))}")


if __name__ == "__main__":
    main()
