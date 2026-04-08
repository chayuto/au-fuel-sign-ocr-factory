#!/usr/bin/env python3
"""Process images from data/ingest/ into data/tmp/ for labeling.

This is the bridge between scrape agents (who write to data/ingest/) and
labeling agents (who read from data/tmp/). It handles dedup, move, manifest
registration, and ingest cleanup.

Three levels of dedup:
  1. Filename match — exact name already in data/tmp/ or manifest
  2. SHA-256 hash — identical file content under a different name
  3. Perceptual hash (pHash) — visually similar image (resized, recompressed, cropped)

Usage:
    python .claude/skills/data-pipeline/scripts/process_ingest.py [--dry-run] [--phash-threshold 10]

Flags:
    --dry-run              Show what would happen without making changes
    --phash-threshold N    Max pHash distance to consider duplicate (default: 10)
                           0-10: same image, different resolution/compression
                           10-25: very similar (same scene, slight crop)
                           25+: different images
"""

import argparse
import csv
import hashlib
import shutil
import sys
from pathlib import Path

try:
    import imagehash
    from PIL import Image
    HAS_PHASH = True
except ImportError:
    HAS_PHASH = False

INGEST_DIR = Path("data/ingest")
TMP_DIR = Path("data/tmp")
MANIFEST = TMP_DIR / "labeling_manifest.csv"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

DEFAULT_PHASH_THRESHOLD = 10  # distance <= this = duplicate


def find_ingest_images() -> list[Path]:
    """Find all image files in data/ingest/ (recursive, across batch dirs)."""
    images = []
    if not INGEST_DIR.exists():
        return images
    for path in sorted(INGEST_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            images.append(path)
    return images


def load_manifest_filenames() -> set[str]:
    """Load all filenames already in the manifest."""
    filenames = set()
    if not MANIFEST.exists():
        return filenames
    with open(MANIFEST) as f:
        for row in csv.DictReader(f):
            filenames.add(row["filename"])
    return filenames


def load_tmp_filenames() -> set[str]:
    """Load all image filenames in data/tmp/."""
    filenames = set()
    if not TMP_DIR.exists():
        return filenames
    for path in TMP_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            filenames.add(path.name)
    return filenames


def file_hash(path: Path) -> str:
    """SHA-256 hash of file contents for exact dedup."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_content_dup(ingest_path: Path, tmp_dir: Path) -> str | None:
    """Check if any file in tmp has identical content. Returns matching filename or None."""
    ingest_hash = file_hash(ingest_path)
    ingest_size = ingest_path.stat().st_size
    for tmp_path in tmp_dir.iterdir():
        if tmp_path.is_file() and tmp_path.suffix.lower() in IMAGE_EXTS:
            if tmp_path.stat().st_size == ingest_size:
                if file_hash(tmp_path) == ingest_hash:
                    return tmp_path.name
    return None


def build_phash_index(tmp_dir: Path) -> list[tuple[str, "imagehash.ImageHash"]]:
    """Build perceptual hash index of all images in data/tmp/."""
    if not HAS_PHASH:
        return []
    index = []
    for path in sorted(tmp_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            try:
                h = imagehash.phash(Image.open(path), hash_size=16)
                index.append((path.name, h))
            except Exception:
                continue
    return index


def check_phash_dup(
    ingest_path: Path,
    phash_index: list[tuple[str, "imagehash.ImageHash"]],
    threshold: int,
) -> tuple[str, int] | None:
    """Check if image is perceptually similar to any in the index.

    Returns (matching_filename, distance) or None.
    """
    if not HAS_PHASH or not phash_index:
        return None
    try:
        h = imagehash.phash(Image.open(ingest_path), hash_size=16)
    except Exception:
        return None

    best_match = None
    best_dist = threshold + 1
    for name, existing_h in phash_index:
        dist = h - existing_h
        if dist < best_dist:
            best_dist = dist
            best_match = name
    if best_dist <= threshold:
        return (best_match, best_dist)
    return None


def process(dry_run: bool = False, phash_threshold: int = DEFAULT_PHASH_THRESHOLD) -> dict:
    """Process all images in ingest. Returns summary dict."""
    results = {
        "added": [],
        "dup_name": [],
        "dup_content": [],
        "dup_phash": [],
        "too_small": [],
        "errors": [],
    }

    ingest_images = find_ingest_images()
    if not ingest_images:
        print("No images found in data/ingest/")
        return results

    print(f"Found {len(ingest_images)} images in data/ingest/")

    manifest_names = load_manifest_filenames()
    tmp_names = load_tmp_filenames()

    # Build perceptual hash index (one-time cost)
    if HAS_PHASH:
        print(f"Building perceptual hash index for {len(tmp_names)} images in data/tmp/...")
        phash_index = build_phash_index(TMP_DIR)
        print(f"  Indexed {len(phash_index)} images (pHash threshold={phash_threshold})")
    else:
        print("  Warning: imagehash not installed, skipping perceptual dedup")
        print("  Install with: pip install imagehash")
        phash_index = []

    new_manifest_rows = []

    for img_path in ingest_images:
        name = img_path.name

        # Check file size (>1KB)
        if img_path.stat().st_size < 1024:
            print(f"  SKIP (too small): {name} ({img_path.stat().st_size} bytes)")
            results["too_small"].append(name)
            continue

        # Level 1: Filename match
        if name in tmp_names or name in manifest_names:
            print(f"  DUP (name): {name}")
            results["dup_name"].append(name)
            continue

        # Level 2: Content hash (exact bytes)
        content_match = check_content_dup(img_path, TMP_DIR)
        if content_match:
            print(f"  DUP (sha256): {name} = {content_match}")
            results["dup_content"].append((name, content_match))
            continue

        # Level 3: Perceptual hash (visual similarity)
        phash_match = check_phash_dup(img_path, phash_index, phash_threshold)
        if phash_match:
            match_name, dist = phash_match
            print(f"  DUP (phash, dist={dist}): {name} ~ {match_name}")
            results["dup_phash"].append((name, match_name, dist))
            continue

        # Passed all checks — new image
        dest = TMP_DIR / name
        print(f"  ADD: {name}")
        if not dry_run:
            try:
                shutil.copy2(img_path, dest)
                new_manifest_rows.append(name)
                tmp_names.add(name)
                manifest_names.add(name)
                # Add to phash index so later ingest images dedup against it
                if HAS_PHASH:
                    try:
                        h = imagehash.phash(Image.open(dest), hash_size=16)
                        phash_index.append((name, h))
                    except Exception:
                        pass
            except Exception as e:
                print(f"  ERROR copying {name}: {e}")
                results["errors"].append((name, str(e)))
                continue
        results["added"].append(name)

    # Append to manifest
    if new_manifest_rows and not dry_run:
        with open(MANIFEST, "a") as f:
            for name in new_manifest_rows:
                f.write(f"{name},pending,,,,,,\n")
        print(f"\nAdded {len(new_manifest_rows)} rows to manifest")

    # Archive scrape reports before cleaning
    reports_dir = Path("docs/scrape_reports")
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        for md_path in INGEST_DIR.rglob("*.md"):
            batch_name = md_path.parent.name
            dest = reports_dir / f"{batch_name}_{md_path.name}"
            shutil.copy2(md_path, dest)
            md_path.unlink()
            print(f"  Archived report: {dest.name}")

    # Clean up ingest
    if not dry_run:
        all_processed = (
            set(results["added"])
            | set(results["dup_name"])
            | {d[0] for d in results["dup_content"]}
            | {d[0] for d in results["dup_phash"]}
            | set(results["too_small"])
        )
        cleaned = 0
        for img_path in ingest_images:
            if img_path.exists() and img_path.name in all_processed:
                img_path.unlink()
                cleaned += 1
        # Remove empty batch directories (but never data/ingest/ itself)
        if INGEST_DIR.exists():
            for d in sorted(INGEST_DIR.rglob("*"), reverse=True):
                if d.is_dir() and d != INGEST_DIR and not any(d.iterdir()):
                    d.rmdir()
        print(f"Cleaned {cleaned} files from ingest")

    return results


def main():
    parser = argparse.ArgumentParser(description="Process ingest images into data/tmp/")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without making changes")
    parser.add_argument("--phash-threshold", type=int, default=DEFAULT_PHASH_THRESHOLD,
                        help=f"Max pHash distance to flag as duplicate (default: {DEFAULT_PHASH_THRESHOLD})")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN ===\n")

    results = process(dry_run=args.dry_run, phash_threshold=args.phash_threshold)

    print(f"\n{'='*40}")
    print(f"Summary:")
    print(f"  Added:         {len(results['added'])}")
    print(f"  Dup (name):    {len(results['dup_name'])}")
    print(f"  Dup (sha256):  {len(results['dup_content'])}")
    print(f"  Dup (phash):   {len(results['dup_phash'])}")
    print(f"  Too small:     {len(results['too_small'])}")
    print(f"  Errors:        {len(results['errors'])}")

    if results["dup_phash"]:
        print(f"\nPerceptual duplicates (visually similar):")
        for name, match, dist in results["dup_phash"]:
            print(f"  {name} ~ {match} (distance={dist})")

    # Log to pipeline events
    if not args.dry_run:
        import subprocess
        logger = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "pipeline_logger.py"
        if logger.exists():
            for name in results.get("added", []):
                try:
                    subprocess.run(
                        [sys.executable, str(logger), "log",
                         "--image", name, "--stage", "ingest",
                         "--agent", "process_ingest",
                         "--action", "ingested",
                         "--details", f'{{"dedup_level": "passed_all"}}'],
                        capture_output=True, timeout=5,
                    )
                except Exception:
                    pass
            for name in results.get("dup_content", []):
                try:
                    subprocess.run(
                        [sys.executable, str(logger), "log",
                         "--image", name, "--stage", "ingest",
                         "--agent", "process_ingest",
                         "--action", "dedup_rejected",
                         "--reason", "sha256 duplicate"],
                        capture_output=True, timeout=5,
                    )
                except Exception:
                    pass

    if results["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
