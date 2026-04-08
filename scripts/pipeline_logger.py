#!/usr/bin/env python3
"""
Pipeline Event Logger — Single source of truth for all pipeline events.

Every stage of the pipeline appends structured events here.
Nothing manual — agents call this script, reports are generated from it.

Usage:
    # Log an event
    python scripts/pipeline_logger.py log \
        --image file.jpg --stage label --agent sonnet_v5_cal \
        --model sonnet --prompt-version v5 --action labeled \
        --brand bp --entries 3 --quality B \
        --details '{"sign_type": "led", "time_of_day": "day"}'

    # Log a skip
    python scripts/pipeline_logger.py log \
        --image file.jpg --stage label --agent sonnet_v5_cal \
        --model sonnet --prompt-version v5 --action skipped \
        --reason "not Australian station"

    # Log a fix
    python scripts/pipeline_logger.py log \
        --image file.jpg --stage audit --agent auto_tighten \
        --action fixed --details '{"old_bbox": [...], "new_bbox": [...]}'

    # Generate run report
    python scripts/pipeline_logger.py report --agent sonnet_v5_cal

    # Generate full audit report
    python scripts/pipeline_logger.py audit

    # Query history for one image
    python scripts/pipeline_logger.py history --image file.jpg

    # Get current prompt version
    python scripts/pipeline_logger.py prompt-version
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

LOG_PATH = "data/tmp/pipeline_events.jsonl"
PROMPT_VERSION_PATH = "configs/prompt_version.json"


def get_prompt_version():
    """Get current prompt version from config."""
    if os.path.exists(PROMPT_VERSION_PATH):
        return json.load(open(PROMPT_VERSION_PATH))
    return {
        "version": "v5",
        "date": "2026-04-08",
        "changes": "sign_board scope tightened, quality checklist, Sonnet second-pass gate"
    }


def log_event(args):
    """Append a structured event to the pipeline log."""
    ts = datetime.now(timezone.utc).isoformat()
    prompt_info = get_prompt_version()

    event = {
        "timestamp": ts,
        "image": args.image,
        "stage": args.stage,  # ingest, screen, label, audit, fix, remove
        "agent": args.agent,
        "model": getattr(args, "model", None),
        "prompt_version": getattr(args, "prompt_version", None) or prompt_info["version"],
        "action": args.action,  # labeled, skipped, fixed, tightened, removed, ingested
    }

    # Optional fields
    if getattr(args, "brand", None):
        event["brand"] = args.brand
    if getattr(args, "entries", None):
        event["entries"] = int(args.entries)
    if getattr(args, "quality", None):
        event["quality"] = args.quality
    if getattr(args, "reason", None):
        event["reason"] = args.reason
    if getattr(args, "details", None):
        try:
            event["details"] = json.loads(args.details)
        except json.JSONDecodeError:
            event["details"] = args.details

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")

    print(f"Logged: {args.action} {args.image} by {args.agent}")


def load_events():
    """Load all pipeline events."""
    if not os.path.exists(LOG_PATH):
        return []
    events = []
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def cmd_history(args):
    """Show full history for one image."""
    events = load_events()
    image_events = [e for e in events if e.get("image") == args.image]

    if not image_events:
        print(f"No events found for {args.image}")
        return

    print(f"=== History: {args.image} ({len(image_events)} events) ===\n")
    for e in image_events:
        ts = e.get("timestamp", "?")[:19]
        stage = e.get("stage", "?")
        agent = e.get("agent", "?")
        action = e.get("action", "?")
        model = e.get("model", "")
        pv = e.get("prompt_version", "")
        detail = ""
        if e.get("brand"):
            detail += f" brand={e['brand']}"
        if e.get("entries"):
            detail += f" entries={e['entries']}"
        if e.get("quality"):
            detail += f" quality={e['quality']}"
        if e.get("reason"):
            detail += f" reason={e['reason']}"
        print(f"  {ts} | {stage:6s} | {action:10s} | {agent} ({model} {pv}){detail}")


def cmd_report(args):
    """Generate run report for a specific agent."""
    events = load_events()
    agent_events = [e for e in events if e.get("agent") == args.agent]

    if not agent_events:
        print(f"No events found for agent {args.agent}")
        return

    labeled = [e for e in agent_events if e.get("action") == "labeled"]
    skipped = [e for e in agent_events if e.get("action") == "skipped"]
    total = len(labeled) + len(skipped)

    print(f"=== Run Report: {args.agent} ===\n")
    print(f"Total processed: {total}")
    print(f"Labeled: {len(labeled)} ({100*len(labeled)//max(total,1)}%)")
    print(f"Skipped: {len(skipped)} ({100*len(skipped)//max(total,1)}%)")

    if labeled:
        brands = defaultdict(int)
        for e in labeled:
            brands[e.get("brand", "unknown")] += 1
        print(f"\nBrands labeled: {dict(brands)}")

        models = set(e.get("model", "?") for e in labeled)
        versions = set(e.get("prompt_version", "?") for e in labeled)
        print(f"Model(s): {', '.join(models)}")
        print(f"Prompt version(s): {', '.join(versions)}")

    if skipped:
        reasons = defaultdict(int)
        for e in skipped:
            reasons[e.get("reason", "unknown")[:50]] += 1
        print(f"\nSkip reasons:")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"  {count}x {reason}")


def cmd_audit(args):
    """Full audit report from pipeline events."""
    events = load_events()

    by_stage = defaultdict(int)
    by_action = defaultdict(int)
    by_agent = defaultdict(lambda: {"labeled": 0, "skipped": 0, "fixed": 0})
    by_version = defaultdict(lambda: {"labeled": 0, "skipped": 0})
    by_model = defaultdict(lambda: {"labeled": 0, "skipped": 0})

    for e in events:
        by_stage[e.get("stage", "?")] += 1
        by_action[e.get("action", "?")] += 1

        agent = e.get("agent", "unknown")
        action = e.get("action", "?")
        by_agent[agent][action] = by_agent[agent].get(action, 0) + 1

        version = e.get("prompt_version", "unknown")
        by_version[version][action] = by_version[version].get(action, 0) + 1

        model = e.get("model", "unknown")
        by_model[model][action] = by_model[model].get(action, 0) + 1

    print(f"=== Pipeline Audit ({len(events)} total events) ===\n")

    print("By stage:", dict(by_stage))
    print("By action:", dict(by_action))

    print("\nBy prompt version:")
    for v, counts in sorted(by_version.items()):
        print(f"  {v}: labeled={counts.get('labeled',0)}, skipped={counts.get('skipped',0)}")

    print("\nBy model:")
    for m, counts in sorted(by_model.items()):
        print(f"  {m}: labeled={counts.get('labeled',0)}, skipped={counts.get('skipped',0)}")

    print("\nTop agents (by total events):")
    for agent, counts in sorted(by_agent.items(), key=lambda x: -sum(x[1].values()))[:15]:
        total = sum(counts.values())
        print(f"  {agent:30s}: {total:3d} events (labeled={counts.get('labeled',0)}, skipped={counts.get('skipped',0)})")


def cmd_prompt_version(args):
    """Show current prompt version."""
    pv = get_prompt_version()
    print(json.dumps(pv, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Pipeline Event Logger")
    sub = parser.add_subparsers(dest="command")

    # log command
    p_log = sub.add_parser("log", help="Log a pipeline event")
    p_log.add_argument("--image", required=True)
    p_log.add_argument("--stage", required=True, choices=["ingest", "screen", "label", "audit", "fix", "remove"])
    p_log.add_argument("--agent", required=True)
    p_log.add_argument("--action", required=True)
    p_log.add_argument("--model", default=None)
    p_log.add_argument("--prompt-version", default=None)
    p_log.add_argument("--brand", default=None)
    p_log.add_argument("--entries", default=None)
    p_log.add_argument("--quality", default=None)
    p_log.add_argument("--reason", default=None)
    p_log.add_argument("--details", default=None)

    # history command
    p_hist = sub.add_parser("history", help="Show history for one image")
    p_hist.add_argument("--image", required=True)

    # report command
    p_report = sub.add_parser("report", help="Run report for agent")
    p_report.add_argument("--agent", required=True)

    # audit command
    sub.add_parser("audit", help="Full pipeline audit")

    # prompt-version command
    sub.add_parser("prompt-version", help="Show current prompt version")

    args = parser.parse_args()

    if args.command == "log":
        log_event(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "prompt-version":
        cmd_prompt_version(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
