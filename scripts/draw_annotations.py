#!/usr/bin/env python3
"""Draw annotation bboxes on images for visual review.

Reads JSON annotations and draws color-coded bounding boxes + labels
on each image. Outputs to data/tmp/preview/ for quick visual QA.

Usage:
    # Draw all labeled images
    python scripts/draw_annotations.py

    # Draw specific images
    python scripts/draw_annotations.py --files au_fuel_wiki_7eleven_shortland wiki_caltex_030

    # Draw only images with issues (price outside sign_board, overlap, etc.)
    python scripts/draw_annotations.py --issues-only
"""

import argparse
import csv
import json
import os
from pathlib import Path

import cv2
import numpy as np

SRC_DIR = Path("data/tmp")
ANN_DIR = SRC_DIR / "annotations"
PREVIEW_DIR = SRC_DIR / "preview"
MANIFEST = SRC_DIR / "labeling_manifest.csv"

# Colors (BGR)
COLORS = {
    "sign_board": (0, 255, 0),      # green
    "brand_zone": (255, 165, 0),    # orange
    "fuel_label": (255, 255, 0),    # cyan
    "fuel_price": (0, 0, 255),      # red
}

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.45
THICKNESS = 2
LABEL_THICKNESS = 1


def draw_bbox(img, bbox, color, label_text, h, w):
    """Draw one bbox with label on the image."""
    x1 = int(bbox[0] * w)
    y1 = int(bbox[1] * h)
    x2 = int(bbox[2] * w)
    y2 = int(bbox[3] * h)

    cv2.rectangle(img, (x1, y1), (x2, y2), color, THICKNESS)

    # Label background
    (tw, th), _ = cv2.getTextSize(label_text, FONT, FONT_SCALE, LABEL_THICKNESS)
    cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(img, label_text, (x1 + 2, y1 - 4), FONT, FONT_SCALE, (0, 0, 0), LABEL_THICKNESS)


def check_issues(ann_data):
    """Check annotation for common issues. Returns list of issue strings."""
    issues = []
    sign = ann_data["sign"]
    sb = sign["bbox"]
    entries = ann_data.get("entries", [])

    # sign_board sanity
    sb_w = sb[2] - sb[0]
    sb_h = sb[3] - sb[1]
    if sb_w < 0.05 or sb_h < 0.05:
        issues.append("sign_board too small")
    if sb_w > 0.95 and sb_h > 0.95:
        issues.append("sign_board covers entire image")

    for i, e in enumerate(entries):
        lb = e["label_bbox"]
        pb = e["price_bbox"]

        # Price outside sign_board
        if pb[0] < sb[0] - 0.03 or pb[2] > sb[2] + 0.03 or pb[1] < sb[1] - 0.03 or pb[3] > sb[3] + 0.03:
            issues.append(f"row{i}: price outside sign_board")

        # Label outside sign_board
        if lb[0] < sb[0] - 0.03 or lb[2] > sb[2] + 0.03 or lb[1] < sb[1] - 0.03 or lb[3] > sb[3] + 0.03:
            issues.append(f"row{i}: label outside sign_board")

        # Overlap (label and price overlap)
        gap = pb[0] - lb[2]
        if gap < -0.03:
            issues.append(f"row{i}: label/price overlap (gap={gap:.3f})")

        # Price LEFT of label (wrong spatial order)
        if pb[0] < lb[0] and (pb[2] - pb[0]) > 0.02:
            issues.append(f"row{i}: price LEFT of label")

        # Very large or very small bboxes
        pw = pb[2] - pb[0]
        ph = pb[3] - pb[1]
        if pw > 0.5:
            issues.append(f"row{i}: price bbox too wide ({pw:.3f})")
        if pw < 0.02:
            issues.append(f"row{i}: price bbox too narrow ({pw:.3f})")

        # Y-center mismatch between label and price
        lcy = (lb[1] + lb[3]) / 2
        pcy = (pb[1] + pb[3]) / 2
        if abs(lcy - pcy) > 0.05:
            issues.append(f"row{i}: label/price Y-misaligned (dy={abs(lcy-pcy):.3f})")

    return issues


def draw_one(stem, img_path, ann_path, preview_dir):
    """Draw annotations on one image. Returns (stem, issues_list)."""
    data = json.loads(ann_path.read_text())
    sign = data["sign"]
    entries = data.get("entries", [])

    img = cv2.imread(str(img_path))
    if img is None:
        return stem, ["cannot read image"]
    h, w = img.shape[:2]

    issues = check_issues(data)

    # Draw sign_board
    draw_bbox(img, sign["bbox"], COLORS["sign_board"],
              f"sign_board ({sign['brand']})", h, w)

    # Draw brand_zone
    if "brand_bbox" in sign:
        draw_bbox(img, sign["brand_bbox"], COLORS["brand_zone"], "brand_zone", h, w)

    # Draw entries
    for i, e in enumerate(entries):
        price_label = f"price: {e['price']}"
        draw_bbox(img, e["price_bbox"], COLORS["fuel_price"], price_label, h, w)

        type_label = f"label: {e['fuel_type']} \"{e['display_text']}\""
        draw_bbox(img, e["label_bbox"], COLORS["fuel_label"], type_label, h, w)

    # Draw issue warnings on image
    if issues:
        y_off = h - 10
        for issue in reversed(issues):
            cv2.putText(img, f"!! {issue}", (10, y_off), FONT, 0.5, (0, 0, 255), 2)
            y_off -= 20

    # Draw legend
    legend_y = 20
    for name, color in COLORS.items():
        cv2.rectangle(img, (w - 180, legend_y - 12), (w - 165, legend_y + 2), color, -1)
        cv2.putText(img, name, (w - 160, legend_y), FONT, 0.4, (255, 255, 255), 1)
        legend_y += 18

    # Save
    out_path = preview_dir / f"{stem}_preview.jpg"
    cv2.imwrite(str(out_path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return stem, issues


def main():
    parser = argparse.ArgumentParser(description="Draw annotation bboxes on images")
    parser.add_argument("--files", nargs="*", help="Specific stems to draw (default: all labeled)")
    parser.add_argument("--issues-only", action="store_true", help="Only draw images with detected issues")
    parser.add_argument("--output", default=str(PREVIEW_DIR), help="Output directory")
    args = parser.parse_args()

    preview_dir = Path(args.output)
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Get list of files to process
    if args.files:
        stems = args.files
    else:
        # All labeled images from manifest
        stems = []
        with open(MANIFEST) as f:
            for row in csv.DictReader(f):
                if row["status"] == "done":
                    stems.append(os.path.splitext(row["filename"])[0])

    total = 0
    issues_count = 0
    all_issues = []

    for stem in stems:
        ann_path = ANN_DIR / f"{stem}.json"
        if not ann_path.exists():
            continue

        # Find the image file (could be .jpg, .jpeg, .png)
        img_path = None
        for ext in [".jpg", ".jpeg", ".png"]:
            candidate = SRC_DIR / f"{stem}{ext}"
            if candidate.exists():
                img_path = candidate
                break
        if img_path is None:
            continue

        if args.issues_only:
            data = json.loads(ann_path.read_text())
            issues = check_issues(data)
            if not issues:
                continue

        stem_name, issues = draw_one(stem, img_path, ann_path, preview_dir)
        total += 1
        if issues:
            issues_count += 1
            all_issues.append((stem_name, issues))

    # Summary
    print(f"\nDrawn {total} preview images → {preview_dir}/")
    print(f"Images with issues: {issues_count}/{total}")

    if all_issues:
        print(f"\n{'='*70}")
        print("ISSUES FOUND")
        print(f"{'='*70}")
        for stem, issues in all_issues:
            print(f"\n{stem}:")
            for issue in issues:
                print(f"  - {issue}")

    # Issue type summary
    if all_issues:
        issue_types = {}
        for _, issues in all_issues:
            for issue in issues:
                # Extract issue type (before the parenthetical details)
                itype = issue.split("(")[0].strip()
                if ":" in itype:
                    itype = itype.split(":")[1].strip()
                issue_types[itype] = issue_types.get(itype, 0) + 1

        print(f"\nIssue type summary:")
        for itype, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            print(f"  {count:>3}x  {itype}")


if __name__ == "__main__":
    main()
