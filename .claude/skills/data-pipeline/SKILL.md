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

## The Full Pipeline (2 stages)

```
STAGE 1: INGEST (process_ingest.py)
  data/ingest/ → dedup (name, SHA-256, pHash) → data/tmp/ + manifest (status=pending)

STAGE 2: LABEL (Sonnet agents, batches of 5)
  pending images → Sonnet reads each → screen + annotate in one pass
  skipped → manifest status=skipped (no annotation files created)
  labeled → manifest status=done + annotation JSON + YOLO label + preview
```

**Haiku screening has been RETIRED.** Sonnet does screening as a built-in gate (second-pass
classification before annotation). This is simpler and more reliable than a separate Haiku phase.

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

## After Running process_ingest.py

Report the summary, then proceed to Sonnet labeling:
- If images were added: "N new images ingested. Launching Sonnet labeling..."
- If all were dups: "All images already in the dataset. No new additions."
- If ingest was empty: "Nothing in data/ingest/ to process."

## Stage 2: Sonnet Labeling

After ingest, go straight to Sonnet labeling in batches of 5:
- Max 5 Sonnet agents concurrent (tested safe in production 2026-04-11)
- Each agent screens+labels in one pass (second-pass gate built in)
- Expected yield: 25-40% labeled from Bing scrapes, 40-100% from state+brand queries
- Report: "N labeled, M skipped. Reconcile manifest, then retrain?"

### Interruption Recovery

Agents can be interrupted at any time (rate limits, context overflow, user cancellation).
The pipeline is designed to be **idempotent** — you can always recover by running reconciliation.

**To resume after interruption:**

```bash
# 1. Check what's still pending
awk -F, 'NR>1 && $2=="pending"{c++} END{print "Pending:", c+0}' data/tmp/labeling_manifest.csv

# 2. Reconcile: match annotations on disk to manifest
# (catches anything agents labeled but didn't write to CSV)
.venv/bin/python -c "
import json, os
from datetime import datetime, timezone
manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
fixed = 0
for fn in sorted(os.listdir('data/tmp/annotations')):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d: continue
    fname = fn[:-5] + '.jpg'
    for i, line in enumerate(lines):
        if line.startswith(fname + ',') and ',done,' not in line:
            brand = d['sign'].get('brand', 'unknown')
            stype = d['sign'].get('sign_type', 'led')
            entries = len(d.get('entries', []))
            lines[i] = f'{fname},done,yes,{brand},{stype},{entries},B,recovered,{ts}\n'
            fixed += 1
            break
with open(manifest, 'w') as f: f.writelines(lines)
print(f'Reconciled {fixed} rows')
"

# 3. Merge manifest.json if agents wrote there by mistake
.venv/bin/python -c "
import json, os
from datetime import datetime, timezone
if not os.path.exists('data/tmp/manifest.json'): exit()
mj = json.load(open('data/tmp/manifest.json'))
if not isinstance(mj, dict): exit()
manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
merged = 0
for fn, entry in mj.items():
    for i, line in enumerate(lines):
        if line.startswith(fn + ',') and ',pending,' in line:
            st = entry.get('status', '')
            agent = entry.get('agent_id', 'recovered')
            if st == 'skipped':
                reason = entry.get('skip_reason', '')[:50]
                lines[i] = f'{fn},skipped,no,,,,{reason},{agent},{ts}\n'
                merged += 1
            break
with open(manifest, 'w') as f: f.writelines(lines)
if merged: print(f'Merged {merged} from manifest.json')
"

# 4. Check remaining pending — these are the ones that need re-processing
awk -F, 'NR>1 && $2=="pending"{print $1}' data/tmp/labeling_manifest.csv | wc -l
```

**Key principle:** Annotations on disk are the source of truth, not the manifest.
If an annotation JSON exists with a `sign` key, that image was labeled — even if the
manifest says "pending". Reconciliation fixes the manifest to match disk reality.

**What's safe to re-run:**
- `process_ingest.py` — idempotent, dedup prevents re-adding existing images
- Labeling agents on pending images — they check the image, skip or label
- Reconciliation — just fixes manifest rows, never deletes anything

**What's NOT safe to re-run:**
- Don't re-label images that already have annotations (would overwrite good work)
- Don't re-scrape the same queries (wastes time, all will be deduped)

## Stage 3: Reconcile (MANDATORY after every labeling run)

Multiple concurrent agents cause manifest write clobber. Always reconcile after labeling:

```bash
# Fix manifest rows that have annotations but aren't marked done
.venv/bin/python -c "
import json, os
from datetime import datetime, timezone
manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
fixed = 0
for fn in sorted(os.listdir('data/tmp/annotations')):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d: continue
    fname = fn[:-5] + '.jpg'
    brand = d['sign'].get('brand', 'unknown')
    stype = d['sign'].get('sign_type', 'led')
    entries = len(d.get('entries', []))
    for i, line in enumerate(lines):
        if line.startswith(fname + ',') and ',done,' not in line:
            lines[i] = f'{fname},done,yes,{brand},{stype},{entries},B,recovered,{ts}\n'
            fixed += 1
            break
with open(manifest, 'w') as f: f.writelines(lines)
print(f'Fixed {fixed} rows')
"

# Clean skip-annotation pollution
for f in data/tmp/annotations/*.json; do
  python3 -c "import json; d=json.load(open('$f')); 'sign' not in d and exit(1)" 2>/dev/null || rm -f "$f"
done
```

## Stage 4: Deep Audit (run before training)

Before building a dataset for training, verify pipeline integrity:

```bash
.venv/bin/python -c "
import json, os, csv

ann_dir = 'data/tmp/annotations'
lbl_dir = 'data/tmp/labels'
prev_dir = 'data/tmp/preview'

valid_anns = set()
for f in os.listdir(ann_dir):
    if f.endswith('.json'):
        d = json.load(open(f'{ann_dir}/{f}'))
        if 'sign' in d: valid_anns.add(f[:-5])

lbl_files = set(f[:-4] for f in os.listdir(lbl_dir) if f.endswith('.txt'))
prev_files = set(f.replace('_preview.jpg','') for f in os.listdir(prev_dir) if f.endswith('_preview.jpg'))

manifest_done = set()
with open('data/tmp/labeling_manifest.csv') as f:
    for row in csv.DictReader(f):
        if row['status'] == 'done':
            manifest_done.add(row['filename'].replace('.jpg','').replace('.jpeg',''))

pending = sum(1 for line in open('data/tmp/labeling_manifest.csv') if ',pending,' in line)

issues = []
if valid_anns - lbl_files: issues.append(f'{len(valid_anns - lbl_files)} annotations missing YOLO labels')
if lbl_files - valid_anns: issues.append(f'{len(lbl_files - valid_anns)} orphan YOLO labels')
if pending > 0: issues.append(f'{pending} images still pending')

VALID = {'shell','bp','ampol','caltex','seven_eleven','united','costco','liberty','puma','metro','mobil','otr','apco','eg','independent','unknown','other'}
for stem in valid_anns:
    d = json.load(open(f'{ann_dir}/{stem}.json'))
    b = d['sign'].get('brand','')
    if b not in VALID: issues.append(f'Invalid brand {b} in {stem}')

print(f'Annotations: {len(valid_anns)}, Labels: {len(lbl_files)}, Previews: {len(prev_files)}, Manifest done: {len(manifest_done)}')
if issues:
    print(f'ISSUES ({len(issues)}):')
    for i in issues: print(f'  - {i}')
else:
    print('ALL CLEAN — ready for training')
"
```

This checks:
- Annotation ↔ YOLO label 1:1 correspondence
- No orphan labels or annotations
- No pending images left
- All brands valid
- No skip-annotation pollution

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

## Known Issues & Workarounds (Learned from Production)

### Image format issues
Bing Image Search returns webp, avif, png, and even HTML/JSON files disguised as .jpg.
**Before screening or labeling**, always run format conversion:
```bash
# Convert ALL non-JPEG .jpg files
find data/tmp/ -maxdepth 1 -name '*.jpg' | while read f; do
  mime=$(file -b --mime-type "$f")
  if [ "$mime" != "image/jpeg" ]; then
    sips -s format jpeg "$f" --out "${f}.tmp" && mv "${f}.tmp" "$f"
  fi
done
# Convert PNGs
find data/tmp/ -maxdepth 1 -name '*.png' | while read f; do
  sips -s format jpeg "$f" --out "${f%.png}.jpg" && rm "$f"
done
sed -i '' 's/\.png,/\.jpg,/g' data/tmp/labeling_manifest.csv
# Delete HTML/JSON masquerading as images
find data/tmp/ -maxdepth 1 -name '*.jpg' | while read f; do
  mime=$(file -b --mime-type "$f")
  [[ "$mime" == text/* || "$mime" == application/json ]] && rm "$f"
done
```

### Manifest concurrent write clobber
Multiple labeling agents writing to labeling_manifest.csv simultaneously causes lost updates.
Agents also write to `manifest.json` instead of `labeling_manifest.csv`, or append rows
that don't match the existing format (extra commas, different column order).

**After EVERY labeling run**, reconcile manifest against actual annotation files:
```python
# reconcile_manifest.py — run after every labeling batch
import json, os
from datetime import datetime, timezone

manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
fixed = 0

for fn in sorted(os.listdir('data/tmp/annotations')):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d: continue  # skip-annotation pollution
    fname = fn[:-5] + '.jpg'
    brand = d['sign'].get('brand', 'unknown')
    stype = d['sign'].get('sign_type', 'led')
    entries = len(d.get('entries', []))

    for i, line in enumerate(lines):
        # Match on filename prefix, fix any non-done row
        if line.startswith(fname + ',') and ',done,' not in line:
            lines[i] = f'{fname},done,yes,{brand},{stype},{entries},B,recovered,{ts}\n'
            fixed += 1
            break

with open(manifest, 'w') as f: f.writelines(lines)
print(f'Fixed {fixed} rows')
```

### Skip-annotation pollution
Some Sonnet agents write JSON files to `data/tmp/annotations/` for SKIPPED images.
These files have keys like `usable`, `skip_reason` but no `sign` key, and crash the
dataset builder with `KeyError: 'sign'`.

**After labeling, clean these up:**
```bash
for f in data/tmp/annotations/*.json; do
  python3 -c "import json; d=json.load(open('$f')); 'sign' not in d and exit(1)" 2>/dev/null || rm -f "$f"
done
```

**Prevention:** Tell agents "Only write annotation JSON for LABELED images. Do NOT create
annotation files for skipped images."

### Filename mismatch between prompt and disk
`process_ingest.py` renames files during dedup (different hash than scraper used).
**Never pass filenames via the agent prompt** — they won't match.
Instead, have agents read `labeling_manifest.csv` to get real filenames:
```
"Read data/tmp/labeling_manifest.csv, find rows where column 2 is 'pending'..."
```

### Agent concurrency limits
- **Sonnet labeling:** max 5 parallel agents (tested safe 2026-04-11). 8+ → 529 API overload
- **Opus labeling:** max 3-5 parallel agents (during Sonnet outage)
- **Batch size:** 5 images per agent. Larger batches reduce quality.

### Image path convention
Images are in `data/tmp/{filename}` — NOT `data/tmp/images/`. Some older images may be in
`data/tmp/images/` from the first Bing scrape round. Agents must use `data/tmp/{filename}`.
