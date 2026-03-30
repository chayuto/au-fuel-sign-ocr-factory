#!/usr/bin/env python3
"""Validate annotation JSON files against structural and domain rules.

Runs as a gate — agents call this after writing annotations, before marking done.
Returns exit code 0 if valid, 1 if any errors found.

Usage:
    # Validate one file
    python scripts/validate_annotations.py data/tmp/annotations/image.json

    # Validate all annotations
    python scripts/validate_annotations.py --all

    # Validate and output JSON (for programmatic use)
    python scripts/validate_annotations.py --all --json
"""

import argparse
import json
import sys
from pathlib import Path

ANNOTATIONS_DIR = Path("data/tmp/annotations")

# --- Domain constants ---

VALID_BRANDS = {
    "shell", "bp", "ampol", "caltex", "seven_eleven", "united",
    "costco", "liberty", "puma", "metro", "mobil", "otr", "independent",
}

VALID_FUEL_TYPES = {"U91", "E10", "P95", "P98", "Diesel", "LPG", "AdBlue", "E85"}

VALID_SIGN_TYPES = {"led", "mechanical", "backlit", "digital", "led_pylon"}

VALID_TIME_OF_DAY = {"day", "night", "dusk"}

VALID_WEATHER = {"clear", "overcast", "rain"}

# Australian fuel prices in cents per litre
PRICE_RANGE = {
    "default": (80.0, 350.0),  # petrol/diesel
    "LPG": (40.0, 150.0),
    "AdBlue": (30.0, 200.0),
}

MAX_ENTRIES = 8  # max fuel rows on any sign
MAX_EXPECTED_ENTRIES = 6  # warn above this (unusual but possible)


def validate_bbox(bbox: list, name: str) -> list[str]:
    """Validate a [x1, y1, x2, y2] bounding box."""
    errors = []
    if not isinstance(bbox, list) or len(bbox) != 4:
        errors.append(f"{name}: bbox must be [x1, y1, x2, y2], got {bbox}")
        return errors

    x1, y1, x2, y2 = bbox
    for i, v in enumerate(bbox):
        if not isinstance(v, (int, float)):
            errors.append(f"{name}: bbox[{i}] is not a number: {v}")
            return errors

    if x1 >= x2:
        errors.append(f"{name}: x1 ({x1:.3f}) >= x2 ({x2:.3f})")
    if y1 >= y2:
        errors.append(f"{name}: y1 ({y1:.3f}) >= y2 ({y2:.3f})")
    if any(v < -0.05 or v > 1.05 for v in bbox):
        errors.append(f"{name}: bbox out of [0,1] range: {bbox}")

    # Zero-area check
    w = x2 - x1
    h = y2 - y1
    if w < 0.01 or h < 0.01:
        errors.append(f"{name}: bbox too small ({w:.3f} x {h:.3f})")

    return errors


def validate_annotation(data: dict, filename: str = "") -> tuple[list[str], list[str]]:
    """Validate a single annotation. Returns (errors, warnings)."""
    errors = []
    warnings = []
    prefix = f"[{filename}] " if filename else ""

    # --- Structure ---
    if "image" not in data:
        errors.append(f"{prefix}missing 'image' section")
    if "sign" not in data:
        errors.append(f"{prefix}missing 'sign' section")
        return errors, warnings  # can't validate further

    sign = data["sign"]
    entries = data.get("entries", [])

    # --- Sign section ---
    if "bbox" not in sign:
        errors.append(f"{prefix}sign: missing bbox")
        return errors, warnings

    sb = sign["bbox"]
    errors.extend(validate_bbox(sb, f"{prefix}sign_board"))

    # Brand
    brand = sign.get("brand")
    if brand and brand not in VALID_BRANDS:
        errors.append(f"{prefix}sign: unknown brand '{brand}' — must be one of {sorted(VALID_BRANDS)}")

    # Sign type
    sign_type = sign.get("sign_type")
    if sign_type and sign_type not in VALID_SIGN_TYPES:
        warnings.append(f"{prefix}sign: unusual sign_type '{sign_type}'")

    # Brand bbox (optional)
    if "brand_bbox" in sign and sign["brand_bbox"] is not None:
        errors.extend(validate_bbox(sign["brand_bbox"], f"{prefix}brand_zone"))

    # --- Conditions ---
    conditions = data.get("image", {}).get("conditions", {})
    tod = conditions.get("time_of_day")
    if tod and tod not in VALID_TIME_OF_DAY:
        warnings.append(f"{prefix}conditions: unknown time_of_day '{tod}'")
    weather = conditions.get("weather")
    if weather and weather not in VALID_WEATHER:
        warnings.append(f"{prefix}conditions: unknown weather '{weather}'")

    # --- Only 1 sign per image ---
    # (sign is a single object, not a list — enforced by schema)

    # --- Entry count ---
    if len(entries) > MAX_ENTRIES:
        errors.append(f"{prefix}too many entries: {len(entries)} (max {MAX_ENTRIES})")
    elif len(entries) > MAX_EXPECTED_ENTRIES:
        warnings.append(f"{prefix}{len(entries)} entries — unusual, verify this is correct")

    if len(entries) == 0:
        warnings.append(f"{prefix}no entries — sign_board annotated but no fuel rows")

    # --- Per-entry validation ---
    sb_valid = len(sb) == 4 and sb[0] < sb[2] and sb[1] < sb[3]

    for i, entry in enumerate(entries):
        row = f"{prefix}row[{i}]"

        # Required fields
        if "label_bbox" not in entry:
            errors.append(f"{row}: missing label_bbox")
            continue
        if "price_bbox" not in entry:
            errors.append(f"{row}: missing price_bbox")
            continue

        lb = entry["label_bbox"]
        pb = entry["price_bbox"]

        errors.extend(validate_bbox(lb, f"{row} label"))
        errors.extend(validate_bbox(pb, f"{row} price"))

        # Skip spatial checks if bboxes are malformed
        if len(lb) != 4 or len(pb) != 4:
            continue

        # Fuel type
        ft = entry.get("fuel_type")
        if ft and ft not in VALID_FUEL_TYPES:
            errors.append(f"{row}: unknown fuel_type '{ft}' — must be one of {sorted(VALID_FUEL_TYPES)}")

        # Price range
        price = entry.get("price")
        if price is not None:
            if not isinstance(price, (int, float)):
                errors.append(f"{row}: price is not a number: {price}")
            else:
                lo, hi = PRICE_RANGE.get(ft, PRICE_RANGE["default"])
                if price < lo or price > hi:
                    warnings.append(f"{row}: price {price} outside expected range ({lo}-{hi}) for {ft}")

        # --- Spatial checks (only if sign_board is valid) ---
        if not sb_valid:
            continue

        # Label inside sign_board
        if lb[0] < sb[0] - 0.05 or lb[2] > sb[2] + 0.05 or lb[1] < sb[1] - 0.05 or lb[3] > sb[3] + 0.05:
            errors.append(f"{row}: label bbox outside sign_board")

        # Price inside sign_board
        if pb[0] < sb[0] - 0.05 or pb[2] > sb[2] + 0.05 or pb[1] < sb[1] - 0.05 or pb[3] > sb[3] + 0.05:
            errors.append(f"{row}: price bbox outside sign_board")

        # Label LEFT of price
        if lb[2] > pb[0] + 0.03:
            errors.append(f"{row}: label overlaps or is right of price (label.x2={lb[2]:.3f}, price.x1={pb[0]:.3f})")

        # Y-alignment
        lcy = (lb[1] + lb[3]) / 2
        pcy = (pb[1] + pb[3]) / 2
        if abs(lcy - pcy) > 0.06:
            errors.append(f"{row}: label/price Y-misaligned (label_cy={lcy:.3f}, price_cy={pcy:.3f}, dy={abs(lcy-pcy):.3f})")

    # --- Cross-row checks ---
    if len(entries) >= 2:
        # Check for duplicate Y-positions (rows stacked on top of each other)
        y_centers = []
        for entry in entries:
            pb = entry.get("price_bbox", [0, 0, 0, 0])
            if len(pb) == 4:
                y_centers.append((pb[1] + pb[3]) / 2)

        for j in range(len(y_centers)):
            for k in range(j + 1, len(y_centers)):
                if abs(y_centers[j] - y_centers[k]) < 0.02:
                    warnings.append(f"{prefix}rows {j} and {k} have nearly identical Y-position — possible duplicate")

    return errors, warnings


def validate_file(path: Path) -> tuple[str, list[str], list[str]]:
    """Validate a single annotation file. Returns (filename, errors, warnings)."""
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return path.name, [f"Invalid JSON: {e}"], []
    except Exception as e:
        return path.name, [f"Read error: {e}"], []

    errors, warnings = validate_annotation(data, path.stem)
    return path.stem, errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate annotation files")
    parser.add_argument("files", nargs="*", help="Annotation JSON files to validate")
    parser.add_argument("--all", action="store_true", help="Validate all annotations in data/tmp/annotations/")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--errors-only", action="store_true", help="Only show files with errors")
    args = parser.parse_args()

    paths: list[Path] = []
    if args.all:
        paths = sorted(ANNOTATIONS_DIR.glob("*.json"))
    elif args.files:
        paths = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    total = len(paths)
    error_files = 0
    warning_files = 0
    total_errors = 0
    total_warnings = 0
    results = []

    for path in paths:
        stem, errors, warnings = validate_file(path)
        total_errors += len(errors)
        total_warnings += len(warnings)

        if errors:
            error_files += 1
        if warnings:
            warning_files += 1

        if args.json:
            results.append({
                "file": stem,
                "errors": errors,
                "warnings": warnings,
                "valid": len(errors) == 0,
            })
        elif not args.errors_only or errors:
            if errors or warnings:
                print(f"\n{'FAIL' if errors else 'WARN'} {stem}")
                for e in errors:
                    print(f"  ERROR: {e}")
                for w in warnings:
                    print(f"  WARN:  {w}")

    if args.json:
        output = {
            "total": total,
            "valid": total - error_files,
            "errors": error_files,
            "warnings": warning_files,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"Validated: {total} files")
        print(f"  Valid:    {total - error_files}")
        print(f"  Errors:   {error_files} ({total_errors} issues)")
        print(f"  Warnings: {warning_files} ({total_warnings} issues)")

    sys.exit(1 if error_files > 0 else 0)


if __name__ == "__main__":
    main()
