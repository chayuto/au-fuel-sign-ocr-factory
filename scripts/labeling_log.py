#!/usr/bin/env python3
"""Labeling log — append-only JSONL audit trail for all annotation events.

Each line in data/tmp/labeling_log.jsonl is one event. Events are immutable
once written — corrections show up as new events referencing the same image.

Usage:
    # Backfill from manifest (one-time migration)
    python scripts/labeling_log.py backfill

    # Append a labeling event
    python scripts/labeling_log.py append --file img.jpg --action labeled \
        --agent agent_1 --visual-qa true --brand bp --entries 4 --quality B

    # Append a skip event
    python scripts/labeling_log.py append --file img.jpg --action skipped \
        --agent agent_1 --reason "no price sign visible"

    # Append a correction event (re-label with visual QA)
    python scripts/labeling_log.py append --file img.jpg --action corrected \
        --agent agent_5 --visual-qa true --brand bp --entries 4 --quality A \
        --issues-found "sign_board too wide, price bbox shifted"

    # Merge temp fragments (written when main log was unavailable)
    python scripts/labeling_log.py merge

    # Summary stats
    python scripts/labeling_log.py stats
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("data/tmp/labeling_log.jsonl")
LOG_TEMP_DIR = Path("data/tmp/log_fragments")
MANIFEST_PATH = Path("data/tmp/labeling_manifest.csv")

# Valid actions for log events
ACTIONS = {"labeled", "skipped", "corrected", "relabeled", "verified"}


def make_event(
    filename: str,
    action: str,
    agent: str,
    timestamp: str | None = None,
    visual_qa: bool = False,
    brand: str | None = None,
    sign_type: str | None = None,
    num_entries: int | None = None,
    quality: str | None = None,
    reason: str | None = None,
    issues_found: str | None = None,
    notes: str | None = None,
) -> dict:
    """Create a structured log event."""
    if action not in ACTIONS:
        raise ValueError(f"Invalid action '{action}'. Must be one of: {ACTIONS}")

    event = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "action": action,
        "agent": agent,
        "visual_qa": visual_qa,
    }

    # Labeling details (for labeled/corrected/relabeled)
    if action in {"labeled", "corrected", "relabeled", "verified"}:
        if brand:
            event["brand"] = brand
        if sign_type:
            event["sign_type"] = sign_type
        if num_entries is not None:
            event["num_entries"] = num_entries
        if quality:
            event["quality"] = quality

    # Skip reason
    if action == "skipped" and reason:
        event["reason"] = reason

    # Correction details
    if issues_found:
        event["issues_found"] = issues_found

    if notes:
        event["notes"] = notes

    return event


def _log_writable() -> bool:
    """Check if the main log file is writable (exists and not locked/missing parent)."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Try opening for append — catches permission errors, read-only FS, etc.
        with open(LOG_PATH, "a"):
            return True
    except (OSError, PermissionError):
        return False


def append_event(event: dict) -> None:
    """Append a single event to the log. Falls back to a temp fragment file if
    the main log is unavailable (git checked in, locked, read-only, etc.).
    The main agent can later run `merge` to fold fragments into the main log."""
    line = json.dumps(event, separators=(",", ":")) + "\n"

    if _log_writable():
        with open(LOG_PATH, "a") as f:
            f.write(line)
    else:
        # Write to a per-agent fragment file so concurrent agents don't collide
        LOG_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        agent = event.get("agent", "unknown")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        frag_path = LOG_TEMP_DIR / f"{agent}_{ts}.jsonl"
        with open(frag_path, "a") as f:
            f.write(line)
        print(f"WARNING: Main log unavailable, wrote to fragment: {frag_path}")


def backfill_from_manifest() -> None:
    """One-time migration: create log events from the existing manifest."""
    if not MANIFEST_PATH.exists():
        print(f"Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    existing = set()
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            for line in f:
                if line.strip():
                    evt = json.loads(line)
                    existing.add(evt["filename"])

    count = 0
    with open(MANIFEST_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["filename"]
            if filename in existing:
                continue

            status = row.get("status", "")
            agent = row.get("labeled_by", "unknown")
            ts = row.get("timestamp", "")

            # Determine if this was a visual QA run
            # Agents on 2026-03-30 with individual timestamps used the visual QA workflow
            visual_qa = False
            if ts.startswith("2026-03-30") and agent.startswith("agent_"):
                visual_qa = True

            if status == "done":
                event = make_event(
                    filename=filename,
                    action="labeled",
                    agent=agent,
                    timestamp=ts,
                    visual_qa=visual_qa,
                    brand=row.get("brand") or None,
                    sign_type=row.get("sign_type") or None,
                    num_entries=int(row["num_entries"]) if row.get("num_entries") else None,
                    quality=row.get("quality") or None,
                    notes="backfilled from manifest" if not visual_qa else "backfilled from manifest (visual QA run)",
                )
            elif status == "skipped":
                event = make_event(
                    filename=filename,
                    action="skipped",
                    agent=agent,
                    timestamp=ts,
                    reason=row.get("quality", ""),  # quality field holds skip reason
                )
            elif status == "pending":
                continue  # Don't log pending items
            else:
                continue

            append_event(event)
            count += 1

    print(f"Backfilled {count} events from manifest")


def merge_fragments() -> None:
    """Merge all temp fragment files into the main log, then delete them."""
    if not LOG_TEMP_DIR.exists():
        print("No fragment directory found. Nothing to merge.")
        return

    fragments = sorted(LOG_TEMP_DIR.glob("*.jsonl"))
    if not fragments:
        print("No fragment files found. Nothing to merge.")
        return

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    for frag in fragments:
        with open(frag) as f:
            lines = f.readlines()
        with open(LOG_PATH, "a") as f:
            f.writelines(lines)
        total += len(lines)
        frag.unlink()
        print(f"  Merged {len(lines)} events from {frag.name}")

    # Clean up empty dir
    if not any(LOG_TEMP_DIR.iterdir()):
        LOG_TEMP_DIR.rmdir()

    print(f"Merged {total} events from {len(fragments)} fragment(s) into {LOG_PATH}")


def print_stats() -> None:
    """Print summary statistics from the log."""
    if not LOG_PATH.exists():
        print("No log file found. Run 'backfill' first.")
        return

    events = []
    with open(LOG_PATH) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    if not events:
        print("Log is empty.")
        return

    # Count by action
    action_counts: dict[str, int] = {}
    for e in events:
        action_counts[e["action"]] = action_counts.get(e["action"], 0) + 1

    # Count visual QA
    visual_qa_count = sum(1 for e in events if e.get("visual_qa"))
    no_visual_qa = sum(1 for e in events if e["action"] in {"labeled", "corrected", "relabeled"} and not e.get("visual_qa"))

    # Get unique images that have been labeled
    labeled_images = set()
    corrected_images = set()
    for e in events:
        if e["action"] in {"labeled", "relabeled", "corrected"}:
            labeled_images.add(e["filename"])
        if e["action"] == "corrected":
            corrected_images.add(e["filename"])

    # Latest event per image — what's the current state?
    latest: dict[str, dict] = {}
    for e in events:
        fn = e["filename"]
        if fn not in latest or e["timestamp"] >= latest[fn]["timestamp"]:
            latest[fn] = e

    current_labeled = sum(1 for e in latest.values() if e["action"] in {"labeled", "corrected", "relabeled", "verified"})
    current_skipped = sum(1 for e in latest.values() if e["action"] == "skipped")
    current_qa = sum(1 for e in latest.values() if e["action"] in {"labeled", "corrected", "relabeled", "verified"} and e.get("visual_qa"))

    print("=" * 60)
    print("LABELING LOG SUMMARY")
    print("=" * 60)
    print(f"\nTotal events:        {len(events)}")
    print(f"\nBy action:")
    for action, count in sorted(action_counts.items()):
        print(f"  {action:20s} {count:4d}")

    print(f"\nCurrent state (latest event per image):")
    print(f"  Labeled:           {current_labeled:4d}")
    print(f"  Skipped:           {current_skipped:4d}")
    print(f"  With visual QA:    {current_qa:4d}")
    print(f"  Without visual QA: {current_labeled - current_qa:4d}  ← need re-labeling")

    print(f"\nImages corrected:    {len(corrected_images):4d}")
    print(f"Visual QA events:    {visual_qa_count:4d}")
    print(f"Non-QA labels:       {no_visual_qa:4d}")

    # Brand distribution of labeled images
    brand_counts: dict[str, int] = {}
    for e in latest.values():
        if e["action"] in {"labeled", "corrected", "relabeled", "verified"}:
            brand = e.get("brand", "unknown")
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

    if brand_counts:
        print(f"\nBrand distribution (current labels):")
        for brand, count in sorted(brand_counts.items(), key=lambda x: -x[1]):
            print(f"  {brand:20s} {count:4d}")


def main():
    parser = argparse.ArgumentParser(description="Labeling log management")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("backfill", help="Backfill log from manifest")
    sub.add_parser("merge", help="Merge temp fragment files into main log")
    sub.add_parser("stats", help="Print summary statistics")

    ap = sub.add_parser("append", help="Append a log event")
    ap.add_argument("--file", required=True, help="Image filename")
    ap.add_argument("--action", required=True, choices=sorted(ACTIONS))
    ap.add_argument("--agent", required=True, help="Agent ID")
    ap.add_argument("--visual-qa", type=lambda x: x.lower() == "true", default=False)
    ap.add_argument("--brand", default=None)
    ap.add_argument("--sign-type", default=None)
    ap.add_argument("--entries", type=int, default=None)
    ap.add_argument("--quality", default=None)
    ap.add_argument("--reason", default=None)
    ap.add_argument("--issues-found", default=None)
    ap.add_argument("--notes", default=None)

    args = parser.parse_args()

    if args.command == "backfill":
        backfill_from_manifest()
    elif args.command == "merge":
        merge_fragments()
    elif args.command == "stats":
        print_stats()
    elif args.command == "append":
        event = make_event(
            filename=args.file,
            action=args.action,
            agent=args.agent,
            visual_qa=args.visual_qa,
            brand=args.brand,
            sign_type=args.sign_type,
            num_entries=args.entries,
            quality=args.quality,
            reason=args.reason,
            issues_found=args.issues_found,
            notes=args.notes,
        )
        append_event(event)
        print(f"Logged: {event['action']} {event['filename']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
