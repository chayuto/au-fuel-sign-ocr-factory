---
name: data-pipeline
description: |
  Manages the flow of scraped fuel sign images from data/ingest/ into the labeling pipeline
  at data/tmp/. Handles dedup (by filename and content hash), manifest registration, and
  ingest cleanup. Use this skill whenever the user mentions "process ingest", "check ingest",
  "new images", "move scraped images", "run pipeline", "ingest to tmp", or asks about images
  waiting to be processed. Also trigger when the user wants to know what's in data/ingest/,
  or after a scraping session when images need to be moved into the labeling queue.
---

# Data Pipeline: Ingest to Labeling Queue

## What This Does

Scrape agents deposit raw images into `data/ingest/` in batch directories. This pipeline
moves them into `data/tmp/` (the gold dataset directory) where labeling agents pick them up.

The key guarantee: **no duplicates enter the labeling queue**, and **ingest is cleaned after
processing** so images are never re-processed.

## The Pipeline

```
data/ingest/
  batch_20260330T075600/
    wiki_bp_mullaloo_wa.jpg
    wiki_puma_morven_qld_2024_01.jpg
  batch_20260330T105059/
    news_9news_bp_price_board_green_led.jpg

  ↓  process_ingest.py  ↓

data/tmp/
  wiki_bp_mullaloo_wa.jpg          (new)
  wiki_puma_morven_qld_2024_01.jpg (new)
  news_9news_bp_price_board_green_led.jpg (new)

data/tmp/labeling_manifest.csv
  + 3 new rows with status=pending

data/ingest/
  (empty — cleaned up)
```

## How to Run

```bash
# Process all images in data/ingest/
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py

# Preview what would happen without making changes
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --dry-run

# Stricter visual dedup (lower threshold = more aggressive)
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --phash-threshold 5

# Looser visual dedup (catches different angles of same station)
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --phash-threshold 25
```

Requires: `pip install imagehash` (falls back to SHA-256 only if not installed).

The script handles everything in one pass:

1. **Scan** — finds all images in `data/ingest/` (recursive, all batch dirs)
2. **Filter** — skips files under 1KB (corrupt/empty downloads)
3. **Dedup level 1: filename** — exact name match against `data/tmp/` and manifest
4. **Dedup level 2: SHA-256** — identical bytes under a different name
5. **Dedup level 3: perceptual hash** — visually similar images (resized, recompressed, cropped)
6. **Move** — copies new images to `data/tmp/`
7. **Register** — appends to `labeling_manifest.csv` with `status=pending`
8. **Clean** — removes processed files from ingest, deletes empty batch dirs

### Perceptual Hash Dedup

The killer feature. Uses `imagehash` (pHash, 16x16) to detect visually identical images even when:
- Different resolution or compression quality
- Different filename
- Slight crop differences

Distance thresholds (configurable via `--phash-threshold`):
- **0-10** (default threshold): same image, different encoding — **DUPLICATE**
- **10-25**: very similar, same scene with slight angle/crop change
- **25+**: different images

The index is built once over `data/tmp/` (~800 images takes a few seconds), then each ingest
image is compared against it. New images that pass all checks are added to the index so
within-batch dedup also works.

## When to Use

Run this pipeline:
- After a scraping session (scrape agents committed images to `data/ingest/`)
- Before starting a labeling session (to pick up any new images)
- When the user asks "are there new images?" or "what's in ingest?"

## After Running

Report the summary to the user, then suggest next steps:
- If images were added: "N new images added to the labeling queue. Want to start labeling?"
- If all were dups: "All images already in the dataset. No new additions."
- If ingest was empty: "Nothing in data/ingest/ to process."

## Architecture Context

`data/ingest/` is the **only git-tracked directory** under `data/`. This is by design — it's the
sole channel for ephemeral scrape agents (running in worktrees or subagents) to pass images back
to the central repo via git commits. Everything else under `data/` is gitignored and local-only.

The flow: scrape agent commits to `data/ingest/` → main agent pulls → this pipeline moves to
`data/tmp/` → labeling agents annotate from `data/tmp/`.

After processing, images are removed from `data/ingest/` so they don't get re-processed on the
next run, but the directory itself is preserved (git needs it).

## Safety

- Never modifies images in `data/tmp/` — only adds new ones
- Never modifies existing manifest rows — only appends new pending rows
- Preserves `data/ingest/` directory (only removes files and empty batch subdirs)
- Dry-run mode available for preview
- Content hash dedup prevents sneaky duplicates (same image, different filename)
