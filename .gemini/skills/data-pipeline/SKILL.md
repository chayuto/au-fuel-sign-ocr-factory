---
name: data-pipeline
description: |
  Manages the flow of scraped fuel sign images from data/ingest/ into the labeling pipeline
  at data/tmp/. Handles dedup (by filename and content hash), manifest registration, and
  ingest cleanup. Use this skill when the user mentions "process ingest", "check ingest",
  "new images", "move scraped images", "run pipeline", "ingest to tmp", or asks about images
  waiting to be processed.
---

# Data Pipeline: Ingest to Labeling Queue (Gemini Way)

## What This Does

Scrape agents deposit raw images into `data/ingest/` in batch directories. This pipeline
moves them into `data/tmp/` (the gold dataset directory) where labeling agents pick them up.

The key guarantee: **no duplicates enter the labeling queue**, and **ingest is cleaned after
processing** so images are never re-processed.

## The Full Pipeline (2 stages)

```
STAGE 1: INGEST (process_ingest.py)
  data/ingest/ → dedup (name, SHA-256, pHash) → data/tmp/ + manifest (status=pending)

STAGE 2: LABEL (Gemini agents, batches of 5)
  pending images → Gemini reads each → screen + annotate in one pass
  skipped → manifest status=skipped (no annotation files created)
  labeled → manifest status=done + annotation JSON + YOLO label + preview
```

## How to Run

```bash
# Process all images in data/ingest/
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py

# Preview what would happen without making changes
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --dry-run

# Stricter visual dedup (lower threshold = more aggressive)
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --phash-threshold 5
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

## After Running process_ingest.py

Report the summary, then proceed to Gemini labeling:
- If images were added: "N new images ingested. Launching Gemini labeling..."
- If all were dups: "All images already in the dataset. No new additions."
- If ingest was empty: "Nothing in data/ingest/ to process."

## Stage 2: Gemini Labeling

After ingest, go straight to Gemini labeling in batches of 5:
- Use `generalist` or specialized `fuel-sign-labeler` agents.
- Each agent screens+labels in one pass.
- Expected yield: 25-40% labeled from Bing scrapes, 40-100% from state+brand queries.

## Stage 3: Reconcile (MANDATORY after every labeling run)

Multiple concurrent agents cause manifest write clobber. Always reconcile after labeling:

```bash
# Reconcile using the dedicated script
.venv/bin/python scripts/reconcile_manifest.py

# Clean skip-annotation pollution
for f in data/tmp/annotations/*.json; do
  python3 -c "import json; d=json.load(open('$f')); 'sign' not in d and exit(1)" 2>/dev/null || rm -f "$f"
done
```
