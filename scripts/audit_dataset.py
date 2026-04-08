#!/usr/bin/env python3
"""
Dataset Quality Audit Tool

Usage:
    # Full automated audit (all annotations)
    python scripts/audit_dataset.py --full

    # Random sample audit (10 images)
    python scripts/audit_dataset.py --sample 10

    # Audit specific image
    python scripts/audit_dataset.py --file gimg_costco_0b630f18_11.jpg

    # Trace provenance of an annotation
    python scripts/audit_dataset.py --trace gimg_costco_0b630f18_11.jpg

    # Quality distribution report
    python scripts/audit_dataset.py --report
"""

import argparse
import json
import os
import random
import csv
from datetime import datetime, timezone
from pathlib import Path


def load_manifest():
    """Load labeling manifest as list of dicts."""
    manifest_path = "data/tmp/labeling_manifest.csv"
    rows = []
    with open(manifest_path) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                rows.append({
                    "filename": parts[0],
                    "status": parts[1],
                    "has_sign": parts[2] if len(parts) > 2 else "",
                    "brand": parts[3] if len(parts) > 3 else "",
                    "sign_type": parts[4] if len(parts) > 4 else "",
                    "entries": parts[5] if len(parts) > 5 else "",
                    "quality": parts[6] if len(parts) > 6 else "",
                    "agent": parts[7] if len(parts) > 7 else "",
                    "timestamp": parts[8] if len(parts) > 8 else "",
                })
    return rows


def load_annotation(stem):
    """Load annotation JSON for a given stem."""
    path = f"data/tmp/annotations/{stem}.json"
    if not os.path.exists(path):
        return None
    return json.load(open(path))


def check_annotation_quality(stem, ann):
    """Run automated quality checks on one annotation. Returns (grade, issues)."""
    issues = []

    if "sign" not in ann:
        return "INVALID", ["no 'sign' key — skip annotation in annotations/"]

    sb = ann["sign"]["bbox"]
    entries = ann.get("entries", [])

    if not entries:
        return "BAD", ["no fuel entries"]

    sb_area = (sb[2] - sb[0]) * (sb[3] - sb[1])

    # Fuel entry bounds
    all_y1 = min(e["label_bbox"][1] for e in entries)
    all_y2 = max(e["price_bbox"][3] for e in entries)
    all_x1 = min(e["label_bbox"][0] for e in entries)
    all_x2 = max(e["price_bbox"][2] for e in entries)
    entry_area = (all_x2 - all_x1) * (all_y2 - all_y1)

    ratio = sb_area / entry_area if entry_area > 0 else 999

    # sign_board scope
    top_gap = all_y1 - sb[1]
    bottom_gap = sb[3] - all_y2

    if ratio > 3.0:
        issues.append(f"sign_board {ratio:.1f}x bigger than entries")
    if top_gap > 0.15:
        issues.append(f"sign_board extends {top_gap:.2f} above first entry")
    if bottom_gap > 0.15:
        issues.append(f"sign_board extends {bottom_gap:.2f} below last entry")
    if sb_area > 0.5:
        issues.append(f"sign_board covers {sb_area:.0%} of image")

    # Entries inside sign_board
    for i, e in enumerate(entries):
        if e["label_bbox"][0] < sb[0] - 0.03:
            issues.append(f"entry {i} label left of sign_board")
        if e["price_bbox"][2] > sb[2] + 0.03:
            issues.append(f"entry {i} price right of sign_board")
        if e["label_bbox"][1] < sb[1] - 0.03:
            issues.append(f"entry {i} above sign_board")
        if e["price_bbox"][3] > sb[3] + 0.03:
            issues.append(f"entry {i} below sign_board")

    # Label LEFT of price
    for i, e in enumerate(entries):
        if e["label_bbox"][2] > e["price_bbox"][0] + 0.02:
            issues.append(f"entry {i} label overlaps price (label.x2={e['label_bbox'][2]:.3f} > price.x1={e['price_bbox'][0]:.3f})")

    # Price range
    for i, e in enumerate(entries):
        price = e.get("price", 0)
        ftype = e.get("fuel_type", "")
        if ftype == "LPG":
            if price < 30 or price > 200:
                issues.append(f"entry {i} LPG price {price} outside 30-200 range")
        else:
            if price < 70 or price > 350:
                issues.append(f"entry {i} price {price} outside 70-350 range")

    # Provenance
    if not ann.get("prompt_version"):
        issues.append("missing prompt_version field")

    # Grade
    if len(issues) >= 2:
        return "BAD", issues
    elif len(issues) == 1:
        return "OK", issues
    else:
        return "GOOD", []


def get_provenance(filename, manifest_rows, ann):
    """Get full provenance trace for an annotation."""
    trace = {
        "filename": filename,
        "image_path": None,
        "annotation_path": None,
        "label_path": None,
        "preview_path": None,
    }

    stem = filename.rsplit(".", 1)[0]

    # File existence
    for path in [f"data/tmp/{filename}", f"data/tmp/images/{filename}"]:
        if os.path.exists(path):
            trace["image_path"] = path
            trace["image_size_kb"] = os.path.getsize(path) // 1024
            break

    ann_path = f"data/tmp/annotations/{stem}.json"
    if os.path.exists(ann_path):
        trace["annotation_path"] = ann_path

    label_path = f"data/tmp/labels/{stem}.txt"
    if os.path.exists(label_path):
        trace["label_path"] = label_path
        trace["yolo_lines"] = len(open(label_path).readlines())

    preview_path = f"data/tmp/preview/{stem}_preview.jpg"
    if os.path.exists(preview_path):
        trace["preview_path"] = preview_path

    # Manifest info
    for row in manifest_rows:
        if row["filename"] == filename:
            trace["manifest_status"] = row["status"]
            trace["manifest_brand"] = row["brand"]
            trace["manifest_agent"] = row["agent"]
            trace["manifest_timestamp"] = row["timestamp"]
            trace["manifest_quality"] = row["quality"]
            break

    # Annotation provenance
    if ann:
        trace["prompt_version"] = ann.get("prompt_version", "UNKNOWN")
        trace["source"] = ann.get("image", {}).get("source", "UNKNOWN")
        trace["brand"] = ann.get("sign", {}).get("brand", "UNKNOWN")
        trace["sign_type"] = ann.get("sign", {}).get("sign_type", "UNKNOWN")
        trace["num_entries"] = len(ann.get("entries", []))
        trace["conditions"] = ann.get("image", {}).get("conditions", {})

    return trace


def cmd_full(args):
    """Full automated audit of all annotations."""
    ann_dir = "data/tmp/annotations"
    results = {"GOOD": 0, "OK": 0, "BAD": 0, "INVALID": 0}
    all_issues = []

    for fn in sorted(os.listdir(ann_dir)):
        if not fn.endswith(".json"):
            continue
        stem = fn[:-5]
        ann = json.load(open(f"{ann_dir}/{fn}"))
        grade, issues = check_annotation_quality(stem, ann)
        results[grade] += 1
        if issues:
            all_issues.append((stem, grade, issues))

    total = sum(results.values())
    print(f"=== Full Audit: {total} annotations ===")
    print(f"GOOD:    {results['GOOD']} ({100*results['GOOD']//total}%)")
    print(f"OK:      {results['OK']} ({100*results['OK']//total}%)")
    print(f"BAD:     {results['BAD']} ({100*results['BAD']//total}%)")
    print(f"INVALID: {results['INVALID']} ({100*results['INVALID']//total}%)")
    print()

    if all_issues:
        print(f"=== Issues ({len(all_issues)} annotations) ===")
        for stem, grade, issues in all_issues:
            print(f"  [{grade}] {stem}: {'; '.join(issues)}")


def cmd_sample(args):
    """Random sample audit."""
    ann_dir = "data/tmp/annotations"
    files = [f for f in os.listdir(ann_dir) if f.endswith(".json")]
    sample = random.sample(files, min(args.sample, len(files)))
    manifest = load_manifest()

    print(f"=== Random Sample: {len(sample)} annotations ===\n")
    for fn in sample:
        stem = fn[:-5]
        ann = json.load(open(f"{ann_dir}/{fn}"))
        grade, issues = check_annotation_quality(stem, ann)
        trace = get_provenance(stem + ".jpg", manifest, ann)

        print(f"--- {stem} [{grade}] ---")
        print(f"  Brand: {trace.get('brand', '?')}, Type: {trace.get('sign_type', '?')}, Entries: {trace.get('num_entries', '?')}")
        print(f"  Agent: {trace.get('manifest_agent', '?')}, Prompt: {trace.get('prompt_version', '?')}")
        print(f"  Date: {trace.get('manifest_timestamp', '?')}")
        print(f"  Preview: {trace.get('preview_path', 'MISSING')}")
        if issues:
            print(f"  Issues: {'; '.join(issues)}")
        print()


def cmd_trace(args):
    """Full provenance trace for one image."""
    filename = args.trace
    stem = filename.rsplit(".", 1)[0]
    manifest = load_manifest()
    ann = load_annotation(stem)

    trace = get_provenance(filename, manifest, ann)

    print(f"=== Provenance Trace: {filename} ===\n")
    for k, v in trace.items():
        print(f"  {k}: {v}")

    if ann:
        print()
        grade, issues = check_annotation_quality(stem, ann)
        print(f"  Quality grade: {grade}")
        if issues:
            for issue in issues:
                print(f"    - {issue}")


def cmd_report(args):
    """Quality distribution report by agent and prompt version."""
    ann_dir = "data/tmp/annotations"
    manifest = load_manifest()

    by_agent = {}
    by_version = {}
    by_brand = {}

    for fn in sorted(os.listdir(ann_dir)):
        if not fn.endswith(".json"):
            continue
        stem = fn[:-5]
        ann = json.load(open(f"{ann_dir}/{fn}"))
        grade, _ = check_annotation_quality(stem, ann)

        # By prompt version
        version = ann.get("prompt_version", "unknown")
        by_version.setdefault(version, {"GOOD": 0, "OK": 0, "BAD": 0})
        by_version[version][grade] = by_version[version].get(grade, 0) + 1

        # By brand
        brand = ann.get("sign", {}).get("brand", "unknown") if "sign" in ann else "invalid"
        by_brand.setdefault(brand, {"GOOD": 0, "OK": 0, "BAD": 0})
        by_brand[brand][grade] = by_brand[brand].get(grade, 0) + 1

        # By agent (from manifest)
        for row in manifest:
            if row["filename"] == stem + ".jpg":
                agent = row.get("agent", "unknown")
                by_agent.setdefault(agent, {"GOOD": 0, "OK": 0, "BAD": 0})
                by_agent[agent][grade] = by_agent[agent].get(grade, 0) + 1
                break

    print("=== Quality by Prompt Version ===")
    for v, counts in sorted(by_version.items()):
        total = sum(counts.values())
        print(f"  {v}: {counts.get('GOOD',0)}/{total} GOOD ({100*counts.get('GOOD',0)//max(total,1)}%), {counts.get('BAD',0)} BAD")

    print("\n=== Quality by Brand ===")
    for b, counts in sorted(by_brand.items(), key=lambda x: -sum(x[1].values())):
        total = sum(counts.values())
        bad_pct = 100 * counts.get("BAD", 0) // max(total, 1)
        flag = " ⚠" if bad_pct > 10 else ""
        print(f"  {b:15s}: {total:3d} total, {counts.get('GOOD',0):3d} GOOD, {counts.get('BAD',0):2d} BAD ({bad_pct}%){flag}")

    print("\n=== Quality by Agent ===")
    for a, counts in sorted(by_agent.items(), key=lambda x: -sum(x[1].values()))[:15]:
        total = sum(counts.values())
        bad_pct = 100 * counts.get("BAD", 0) // max(total, 1)
        print(f"  {a:25s}: {total:3d} total, {counts.get('GOOD',0):3d} GOOD, {counts.get('BAD',0):2d} BAD ({bad_pct}%)")


def main():
    parser = argparse.ArgumentParser(description="Dataset Quality Audit")
    parser.add_argument("--full", action="store_true", help="Full automated audit")
    parser.add_argument("--sample", type=int, help="Random sample audit (N images)")
    parser.add_argument("--trace", type=str, help="Trace provenance of one image")
    parser.add_argument("--report", action="store_true", help="Quality report by agent/version/brand")
    parser.add_argument("--file", type=str, help="Audit specific file")
    args = parser.parse_args()

    if args.full:
        cmd_full(args)
    elif args.sample:
        cmd_sample(args)
    elif args.trace:
        cmd_trace(args)
    elif args.report:
        cmd_report(args)
    elif args.file:
        args.trace = args.file
        cmd_trace(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
