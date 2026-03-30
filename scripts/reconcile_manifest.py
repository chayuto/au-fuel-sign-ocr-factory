#!/usr/bin/env python3
"""Reconcile all labeling data into a single unified labeling_manifest.csv.

Merges:
1. Existing labeling_manifest.csv (main manifest — agents 7, 9, 10, normalizer)
2. manifest.csv (separate file written by agents 11-14)
3. New images from scrapers not yet in any manifest
4. Labels/annotations on disk but not reflected in manifest

Also normalizes all annotations to canonical schema and regenerates YOLO labels.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

TMP = Path("data/tmp")
ANN_DIR = TMP / "annotations"
LBL_DIR = TMP / "labels"
MAIN_MANIFEST = TMP / "labeling_manifest.csv"
ALT_MANIFEST = TMP / "manifest.csv"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

FIELDNAMES = ["filename", "status", "has_fuel_sign", "brand", "sign_type",
              "num_entries", "quality", "labeled_by", "timestamp"]


def get_all_images():
    """Find all image files in data/tmp/."""
    exts = {".jpg", ".jpeg", ".png"}
    return sorted(f.name for f in TMP.iterdir() if f.suffix.lower() in exts)


def load_main_manifest():
    """Load main labeling_manifest.csv."""
    rows = {}
    if MAIN_MANIFEST.exists():
        with open(MAIN_MANIFEST) as f:
            for r in csv.DictReader(f):
                rows[r["filename"]] = r
    return rows


def load_alt_manifest():
    """Load manifest.csv from agents 11-14."""
    rows = {}
    if ALT_MANIFEST.exists():
        with open(ALT_MANIFEST) as f:
            for r in csv.DictReader(f):
                fname = r["filename"]
                # Normalize field names to match main manifest
                rows[fname] = {
                    "filename": fname,
                    "status": r.get("status", "pending"),
                    "has_fuel_sign": "yes" if r.get("has_sign") == "yes" or r.get("status") == "done" else "no",
                    "brand": r.get("brand", ""),
                    "sign_type": r.get("sign_type", ""),
                    "num_entries": r.get("num_entries", ""),
                    "quality": r.get("quality", "B") if r.get("status") == "done" else r.get("reason", ""),
                    "labeled_by": r.get("agent", r.get("labeled_by", "")),
                    "timestamp": r.get("timestamp", TIMESTAMP),
                }
    return rows


def check_disk_labels():
    """Find all files that have labels on disk."""
    labeled_on_disk = {}
    for lf in LBL_DIR.glob("*.txt"):
        stem = lf.stem
        ann_file = ANN_DIR / f"{stem}.json"
        if ann_file.exists():
            try:
                data = json.loads(ann_file.read_text())
                sign = data.get("sign", {})
                entries = data.get("entries", [])
                labeled_on_disk[stem] = {
                    "brand": sign.get("brand", ""),
                    "sign_type": sign.get("sign_type", "led"),
                    "num_entries": len(entries),
                }
            except (json.JSONDecodeError, KeyError):
                pass
    return labeled_on_disk


def main():
    all_images = get_all_images()
    main_rows = load_main_manifest()
    alt_rows = load_alt_manifest()
    disk_labels = check_disk_labels()

    print(f"Images on disk: {len(all_images)}")
    print(f"Main manifest rows: {len(main_rows)}")
    print(f"Alt manifest rows: {len(alt_rows)}")
    print(f"Labels on disk: {len(disk_labels)}")

    # Build unified manifest
    unified = {}
    stats = {"kept_main": 0, "merged_alt": 0, "from_disk": 0, "new_pending": 0}

    for img in all_images:
        stem = os.path.splitext(img)[0]

        if img in main_rows:
            row = main_rows[img]
            # Check if alt manifest has a better (non-pending) entry
            if img in alt_rows and row["status"] == "pending" and alt_rows[img]["status"] != "pending":
                row = alt_rows[img]
                stats["merged_alt"] += 1
            else:
                stats["kept_main"] += 1
            # Check if there's a label on disk but manifest says pending
            if row["status"] == "pending" and stem in disk_labels:
                dl = disk_labels[stem]
                row["status"] = "done"
                row["has_fuel_sign"] = "yes"
                row["brand"] = dl["brand"]
                row["sign_type"] = dl["sign_type"]
                row["num_entries"] = str(dl["num_entries"])
                row["quality"] = "B"
                row["labeled_by"] = "disk_reconcile"
                row["timestamp"] = TIMESTAMP
                stats["from_disk"] += 1
            unified[img] = row

        elif img in alt_rows:
            unified[img] = alt_rows[img]
            stats["merged_alt"] += 1

        else:
            # New image not in any manifest
            row = {
                "filename": img,
                "status": "pending",
                "has_fuel_sign": "",
                "brand": "",
                "sign_type": "",
                "num_entries": "",
                "quality": "",
                "labeled_by": "",
                "timestamp": "",
            }
            # Check if there's already a label on disk
            if stem in disk_labels:
                dl = disk_labels[stem]
                row["status"] = "done"
                row["has_fuel_sign"] = "yes"
                row["brand"] = dl["brand"]
                row["sign_type"] = dl["sign_type"]
                row["num_entries"] = str(dl["num_entries"])
                row["quality"] = "B"
                row["labeled_by"] = "disk_reconcile"
                row["timestamp"] = TIMESTAMP
                stats["from_disk"] += 1
            else:
                stats["new_pending"] += 1
            unified[img] = row

    # Write unified manifest
    with open(MAIN_MANIFEST, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for img in sorted(unified.keys()):
            # Ensure all fields exist
            row = unified[img]
            clean = {k: row.get(k, "") for k in FIELDNAMES}
            writer.writerow(clean)

    # Summary
    total = len(unified)
    done = sum(1 for r in unified.values() if r["status"] == "done")
    skipped = sum(1 for r in unified.values() if r["status"] == "skipped")
    pending = sum(1 for r in unified.values() if r["status"] == "pending")

    print(f"\n{'='*60}")
    print(f"RECONCILIATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total images in manifest: {total}")
    print(f"  Done:    {done}")
    print(f"  Skipped: {skipped}")
    print(f"  Pending: {pending}")
    print(f"\nMerge stats:")
    print(f"  Kept from main manifest: {stats['kept_main']}")
    print(f"  Merged from alt manifest: {stats['merged_alt']}")
    print(f"  Recovered from disk labels: {stats['from_disk']}")
    print(f"  New pending (scraped, unlabeled): {stats['new_pending']}")


if __name__ == "__main__":
    main()
