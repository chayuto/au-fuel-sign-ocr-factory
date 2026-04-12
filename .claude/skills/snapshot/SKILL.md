---
name: snapshot
description: |
  Creates a full dated backup of all project assets NOT checked into git.
  Captures annotations, labels, images, previews, manifests, configs, experiment docs,
  scrape reports, model weights, and skills — everything needed to restore the full
  project state and continue work. Use when the user says "snapshot", "backup",
  "archive", or "save state".
---

# Project Snapshot — Full Asset Backup

## What Gets Backed Up

Everything NOT in git that's needed to continue the project:

| Category | Path | Why |
|----------|------|-----|
| **Annotations** | `data/tmp/annotations/*.json` | Hours of Sonnet labeling work |
| **YOLO labels** | `data/tmp/labels/*.txt` | Derived from annotations |
| **Raw images** | `data/tmp/*.jpg`, `data/tmp/*.jpeg` | Scraped images, irreplaceable |
| **Preview QC images** | `data/tmp/preview/*.jpg` | Visual verification evidence |
| **Manifests** | `data/tmp/labeling_manifest.csv`, `data/tmp/manifest.json` | Pipeline state |
| **Pipeline events** | `data/tmp/pipeline_events.jsonl` | Full audit trail |
| **Canonical test set** | `configs/canonical_test_v2.json` | Verified test config |
| **Experiment docs** | `docs/experiments/*.md` | Research history |
| **Scrape reports** | `docs/scrape_reports/*.md` | Data provenance |
| **Research docs** | `docs/research/*.md` | External references |
| **Model weights** | `runs/` | Trained model checkpoints |
| **Freeze-split baseline** | `/tmp/finder_baseline/` | Dataset split anchor |
| **Skills** | `.claude/skills/*/` | Agent instructions |
| **Negatives** | `data/negatives/` | Background images |

## How to Run

```bash
DATE=$(date +%Y%m%dT%H%M%S)
BACKUP_DIR="backups/full_${DATE}"
mkdir -p "$BACKUP_DIR"

# 1. Annotations + labels + manifests (small, critical)
tar czf "$BACKUP_DIR/annotations.tar.gz" \
    data/tmp/annotations/ \
    data/tmp/labels/ \
    data/tmp/labeling_manifest.csv \
    data/tmp/manifest.json \
    data/tmp/pipeline_events.jsonl \
    2>/dev/null

# 2. Raw images (large, irreplaceable)
tar czf "$BACKUP_DIR/images.tar.gz" \
    data/tmp/*.jpg data/tmp/*.jpeg \
    2>/dev/null

# 3. Preview QC images (large, regenerable but slow)
tar czf "$BACKUP_DIR/previews.tar.gz" \
    data/tmp/preview/ \
    2>/dev/null

# 4. Untracked docs + configs + skills
tar czf "$BACKUP_DIR/docs_and_config.tar.gz" \
    docs/experiments/ \
    docs/research/ \
    docs/scrape_reports/ \
    docs/model_cards/ \
    docs/ARCHITECTURE_REVIEW_v7.md \
    docs/LABELING_RULES_v7_DRAFT.md \
    configs/canonical_test_v2.json \
    .claude/skills/ml-researcher/ \
    .claude/skills/sign-crop-labeler/ \
    .claude/skills/snapshot/ \
    2>/dev/null

# 5. Model weights (regenerable but expensive)
tar czf "$BACKUP_DIR/model_weights.tar.gz" \
    runs/ \
    2>/dev/null

# 6. Negatives + ingest manifests
tar czf "$BACKUP_DIR/negatives_and_ingest.tar.gz" \
    data/negatives/ \
    data/ingest/*/scrape_manifest.json \
    2>/dev/null

# Summary
echo "=== Snapshot: $BACKUP_DIR ==="
ls -lh "$BACKUP_DIR/"
echo ""
du -sh "$BACKUP_DIR/"
```

## How to Restore

```bash
BACKUP_DIR="backups/full_YYYYMMDDTHHMMSS"

# Restore everything
for f in "$BACKUP_DIR"/*.tar.gz; do
    echo "Restoring $f..."
    tar xzf "$f"
done

echo "Done. Run 'python scripts/build_finder_dataset.py --classes 0 --seed 42' to rebuild dataset."
```

## When to Snapshot

- **Before any destructive operation** (relabeling, dataset rebuild, annotation cleanup)
- **At the end of a session** (preserve progress)
- **Before changing labeling rules** (v5→v6→v7 transitions)
- **Before merging data from multiple sources**
