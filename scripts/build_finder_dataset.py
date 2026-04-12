#!/usr/bin/env python3
"""Build YOLO Finder dataset from labeled images in data/tmp/.

Creates data/finder/ with train/val/test split:
  data/finder/
    images/train/  images/val/  images/test/
    labels/train/  labels/val/  labels/test/
    dataset.yaml

Split: 80/15/5 (stratified by brand to maintain diversity).

Class selection via --classes flag. Annotations always store all 4 classes;
this script selects and remaps for each experiment.

Presets:
  --classes 0,1,2,3   (all 4 — default)
  --classes 0,2,3     (no brand_zone)
  --classes 0,3       (sign_board + fuel_price only)

The original class IDs (0-3) are remapped to contiguous 0..N-1 for YOLO.
"""

import argparse
import csv
import json
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

import yaml

SRC_DIR = Path("data/tmp")
DST_DIR = Path("data/finder")
MANIFEST = SRC_DIR / "labeling_manifest.csv"
SEED = 42

TRAIN_RATIO = 0.80
VAL_RATIO = 0.15
TEST_RATIO = 0.05

ALL_CLASS_NAMES = {0: "sign_board", 1: "brand_zone", 2: "fuel_label", 3: "fuel_price"}


def parse_args():
    parser = argparse.ArgumentParser(description="Build YOLO Finder dataset")
    parser.add_argument(
        "--classes", type=str, default="0,1,2,3",
        help="Comma-separated original class IDs to include (default: 0,1,2,3)"
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output", type=str, default=str(DST_DIR),
                        help="Output directory (default: data/finder)")
    parser.add_argument("--include-list", type=str, default=None,
                        help="File with one image filename per line — only include these images")
    parser.add_argument("--negatives-dir", type=str, default=None,
                        help="Directory of negative images (no signs). Added to train split with empty labels.")
    parser.add_argument("--freeze-split", type=str, default=None,
                        help="Path to a prior image_manifest.json. Val/test splits are frozen; new images go to train only.")
    return parser.parse_args()


def load_labeled_images(include_list: str | None = None):
    """Load all 'done' images from manifest that have annotations on disk.

    If include_list is provided, only images whose filename appears in that
    file will be included (one filename per line).
    """
    allowed = None
    if include_list:
        allowed = set(Path(include_list).read_text().strip().splitlines())
        print(f"Filtering to {len(allowed)} images from {include_list}")

    images = []
    with open(MANIFEST) as f:
        for row in csv.DictReader(f):
            if row["status"] != "done":
                continue
            fname = row["filename"]
            if allowed is not None and fname not in allowed:
                continue
            stem = os.path.splitext(fname)[0]
            img_path = SRC_DIR / fname
            ann_path = SRC_DIR / "annotations" / f"{stem}.json"
            if img_path.exists() and ann_path.exists():
                images.append({
                    "filename": fname,
                    "stem": stem,
                    "brand": row.get("brand", "unknown"),
                    "img_path": img_path,
                    "ann_path": ann_path,
                })
    return images


def annotation_to_yolo_lines(ann_path: Path, class_ids: list[int], class_remap: dict[int, int]) -> list[str]:
    """Convert canonical JSON annotation to YOLO label lines for selected classes.

    Reads from the rich JSON annotation (not the pre-built .txt) so we can
    select and remap classes per experiment.
    """
    data = json.loads(ann_path.read_text())
    sign = data.get("sign", {})
    # Handle alternate schema: sign_board_bbox at top level instead of sign.bbox
    if "bbox" not in sign and "sign_board_bbox" in data:
        sign = {"bbox": data["sign_board_bbox"]}
    entries = data.get("entries", [])
    lines = []

    # Detect pixel coords (values > 1.0) and normalize if needed
    img_w = data.get("image_width", 1)
    img_h = data.get("image_height", 1)
    needs_normalize = any(v > 1.0 for v in sign.get("bbox", [0]))

    def normalize_bbox(bbox: list[float]) -> list[float]:
        if needs_normalize and img_w > 1 and img_h > 1:
            return [bbox[0] / img_w, bbox[1] / img_h, bbox[2] / img_w, bbox[3] / img_h]
        return bbox

    def bbox_to_yolo(bbox: list[float]) -> str:
        bbox = normalize_bbox(bbox)
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return f"{cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"

    # Class 0: sign_board
    if 0 in class_ids:
        lines.append(f"{class_remap[0]} {bbox_to_yolo(sign['bbox'])}")

    # Class 1: brand_zone
    if 1 in class_ids and "brand_bbox" in sign:
        lines.append(f"{class_remap[1]} {bbox_to_yolo(sign['brand_bbox'])}")

    # Class 2 & 3: fuel_label & fuel_price (paired)
    for entry in entries:
        if 2 in class_ids:
            lines.append(f"{class_remap[2]} {bbox_to_yolo(entry['label_bbox'])}")
        if 3 in class_ids:
            lines.append(f"{class_remap[3]} {bbox_to_yolo(entry['price_bbox'])}")

    return lines


def stratified_split(images, seed):
    """Split images by brand to maintain diversity in each set."""
    random.seed(seed)

    by_brand = defaultdict(list)
    for img in images:
        by_brand[img["brand"]].append(img)

    train, val, test = [], [], []

    for brand, items in by_brand.items():
        random.shuffle(items)
        n = len(items)
        n_val = max(1, round(n * VAL_RATIO))
        n_test = max(1, round(n * TEST_RATIO)) if n >= 4 else 0
        n_train = n - n_val - n_test

        if n_train < 1:
            n_train = 1
            n_val = n - n_train - n_test
            if n_val < 0:
                n_val = 0
                n_test = n - n_train

        train.extend(items[:n_train])
        val.extend(items[n_train:n_train + n_val])
        test.extend(items[n_train + n_val:])

    return train, val, test


def write_split(images, split_name, dst_dir, class_ids, class_remap):
    """Generate YOLO labels from JSON annotations and copy images."""
    img_dir = dst_dir / "images" / split_name
    lbl_dir = dst_dir / "labels" / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    for img in images:
        # Copy image
        shutil.copy2(img["img_path"], img_dir / img["filename"])
        # Generate YOLO labels from JSON annotation
        lines = annotation_to_yolo_lines(img["ann_path"], class_ids, class_remap)
        lbl_path = lbl_dir / (img["stem"] + ".txt")
        lbl_path.write_text("\n".join(lines) + "\n" if lines else "")


def count_classes(images, class_ids, class_remap):
    """Count YOLO class instances across a set of images."""
    counts = defaultdict(int)
    for img in images:
        lines = annotation_to_yolo_lines(img["ann_path"], class_ids, class_remap)
        for line in lines:
            cls = int(line.strip().split()[0])
            counts[cls] += 1
    return dict(counts)


def main():
    args = parse_args()

    class_ids = sorted(int(c) for c in args.classes.split(","))
    # Remap to contiguous 0..N-1
    class_remap = {orig: new for new, orig in enumerate(class_ids)}
    class_names = {class_remap[c]: ALL_CLASS_NAMES[c] for c in class_ids}

    dst_dir = Path(args.output)

    print(f"Class config: {class_ids}")
    print(f"  Remap: {', '.join(f'{ALL_CLASS_NAMES[c]}({c})→{class_remap[c]}' for c in class_ids)}")
    print(f"  Names: {class_names}")
    print()

    # Clean previous
    if dst_dir.exists():
        shutil.rmtree(dst_dir)

    images = load_labeled_images(args.include_list)
    print(f"Labeled images with annotations on disk: {len(images)}")

    if len(images) < 10:
        print("ERROR: Too few images for training. Need at least 10.")
        return

    if args.freeze_split:
        # Frozen split: keep val/test from prior manifest, new images → train
        prior = json.loads(Path(args.freeze_split).read_text())
        prior_val = {e["filename"] for e in prior["splits"]["val"]}
        prior_test = {e["filename"] for e in prior["splits"]["test"]}
        train, val, test = [], [], []
        new_to_train = 0
        for img in images:
            if img["filename"] in prior_test:
                test.append(img)
            elif img["filename"] in prior_val:
                val.append(img)
            else:
                train.append(img)
                if img["filename"] not in {e["filename"] for e in prior["splits"]["train"]}:
                    new_to_train += 1
        print(f"\nFrozen split from {args.freeze_split}:")
        print(f"  Prior val/test preserved: {len(val)} val, {len(test)} test")
        print(f"  New images added to train: {new_to_train}")
    else:
        train, val, test = stratified_split(images, args.seed)

    print(f"\nSplit (seed={args.seed}):")
    print(f"  Train: {len(train)} ({len(train)/len(images)*100:.0f}%)")
    print(f"  Val:   {len(val)} ({len(val)/len(images)*100:.0f}%)")
    print(f"  Test:  {len(test)} ({len(test)/len(images)*100:.0f}%)")

    # Write splits
    write_split(train, "train", dst_dir, class_ids, class_remap)
    write_split(val, "val", dst_dir, class_ids, class_remap)
    write_split(test, "test", dst_dir, class_ids, class_remap)

    # Add negative/background images to train split (empty label files)
    n_negatives = 0
    if args.negatives_dir:
        neg_dir = Path(args.negatives_dir)
        train_img_dir = dst_dir / "images" / "train"
        train_lbl_dir = dst_dir / "labels" / "train"
        for img_file in sorted(neg_dir.rglob("*.jpg")):
            shutil.copy2(img_file, train_img_dir / img_file.name)
            (train_lbl_dir / (img_file.stem + ".txt")).write_text("")
            n_negatives += 1
        print(f"\nNegatives added to train: {n_negatives} (from {neg_dir})")
        print(f"  Negative ratio: {n_negatives}/{len(train)+n_negatives} = {n_negatives/(len(train)+n_negatives)*100:.1f}%")

    # Write dataset.yaml
    config = {
        "path": str(dst_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(class_ids),
        "names": class_names,
    }
    yaml_path = dst_dir / "dataset.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Stats
    print(f"\nClass distribution:")
    for split_name, split_images in [("train", train), ("val", val), ("test", test)]:
        counts = count_classes(split_images, class_ids, class_remap)
        parts = ", ".join(f"{class_names[i]}={counts.get(i, 0)}" for i in range(len(class_ids)))
        print(f"  {split_name}: {parts}")

    # Brand distribution
    print(f"\nBrand distribution:")
    for split_name, split_images in [("train", train), ("val", val), ("test", test)]:
        brands = defaultdict(int)
        for img in split_images:
            brands[img["brand"]] += 1
        brand_str = ", ".join(f"{b}={c}" for b, c in sorted(brands.items(), key=lambda x: -x[1]))
        print(f"  {split_name}: {brand_str}")

    # Save frozen image manifest for reproducibility
    from datetime import datetime, timezone
    manifest_data = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "classes": class_ids,
        "negatives_dir": args.negatives_dir,
        "n_negatives": n_negatives,
        "splits": {}
    }
    for split_name, split_images in [("train", train), ("val", val), ("test", test)]:
        manifest_data["splits"][split_name] = [
            {"filename": img["filename"], "brand": img["brand"]} for img in split_images
        ]
    manifest_path = dst_dir / "image_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"\nImage manifest: {manifest_path} ({len(images)} images frozen)")

    print(f"Dataset YAML: {yaml_path}")
    print(f"Output: {dst_dir.resolve()}")


if __name__ == "__main__":
    main()
