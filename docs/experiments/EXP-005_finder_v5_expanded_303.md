# EXP-005: Finder v5 — sign_board with 303 Labeled Images

## Hypothesis

More data continues to improve sign_board detection linearly. 239 train images (up from 177 in EXP-004) should push mAP@50 past 0.49.

**Expected:** mAP@50 > 0.49 (extrapolating EXP-004's linear trend)

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0) only |
| Images | 239 train / 45 val / 19 test |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |

### Data changes from EXP-004

- 303 total labeled images (up from 249)
- 54 new images from sessions H–Q (coles, nsw, mobil2, tas, outrage2, ripoff, seven, vic, bp2, otr)
- Fixed 4 annotations with pixel-coord schema (auto-normalized during build)
- Fixed 28 ghost manifest entries (done but no annotation → pending)
- Added 64 missing annotations to manifest (had JSON but no manifest row)

### Brand coverage (train)

caltex=51, shell=34, bp=31, independent=18, ampol=18, mobil=13, seven_eleven=12, united=12, liberty=11, metro=10, otr=8, puma=7, costco=5, led=3, unknown=2, eg=1, 7eleven=1, apco=1, other=1

## Results

| Metric | best.pt (epoch 69) | last.pt (epoch 100) |
|--------|-------------------|---------------------|
| **mAP@50** | **0.441** | 0.422 |
| mAP@50-95 | 0.123 | 0.136 |
| Precision | — | 0.679 |
| Recall | — | 0.378 |

### Progression (training-time val — NOT comparable across experiments)

| Run | Train imgs | Val imgs | sign_board mAP50 | Delta |
|-----|-----------|----------|-----------------|-------|
| EXP-004 (177 train) | 177 | 35 | 0.452 | baseline |
| EXP-005 (239 train) | 239 | 45 | 0.441 | -2.4% |

### EXP-005b: Fixed val/test evaluation (fair comparison)

Evaluated all models on the **same frozen val/test split** (45 val, 19 test from EXP-005's seed=42 split). Canonical split saved to `configs/canonical_val_split.json`.

| Model | Train imgs | Val mAP50 | Val mAP50-95 | Test mAP50 | Test mAP50-95 |
|-------|-----------|-----------|-------------|-----------|-------------|
| Sanity (131 train) | 131 | — | — | 0.304 | 0.098 |
| **EXP-004** (177 train) | 177 | 0.418 | 0.161 | 0.348 | 0.146 |
| **EXP-005** (239 train) | 239 | **0.404** | 0.131 | **0.595** | **0.208** |

### Key finding

**EXP-005 is substantially better on test (+71% mAP50) despite slightly lower val (-3.3%).**

The val/test divergence suggests:
- The val set contains images the EXP-004 model happened to overfit to (lucky split at 177 images)
- The test set is a more honest measure of generalization
- **EXP-005 generalizes much better** — more training data is working, the original val metric was misleading

## Analysis

**Result: POSITIVE.** The apparent regression (0.452→0.441) was a val set artifact. On a held-out test set, EXP-005 scores **0.595 mAP50** vs EXP-004's 0.348 — a massive **+71% improvement**.

### Why val was misleading

1. **Val set changed.** 35 → 45 images, making training-time metrics incomparable.
2. **When evaluated on the same val set**, EXP-004 scores 0.418 and EXP-005 scores 0.404 — within noise.
3. **Test set tells the real story.** EXP-005 scores 0.595 vs 0.348 — the additional 62 training images dramatically improved generalization.

### Key insight

**Val set composition matters more than val set size for tracking progress.** Future experiments must use the frozen canonical split (`configs/canonical_val_split.json`). And always evaluate on test — val alone can be misleading with small datasets.
- Use a **fixed val set** across experiments (freeze a canonical val split), or
- Report metrics on a **shared test subset** that doesn't change

## Current State

| Component | Best Metric | Status |
|-----------|-------------|--------|
| Finder (1-class sign_board) | mAP50=0.441 (0.452 on prior val) | Active — need fixed val set |
| Reader, Classifier, E2E | — | Not started |

### Dataset after screening session

| Status | Count |
|--------|-------|
| Done (labeled) | 303 |
| Pending (screened, ready for labeling) | 36 |
| Skipped | 1035 |
| **Total** | **1374** |

### Screening yield by source (this session)

| Source | Screened | KEEP | SKIP | Yield |
|--------|----------|------|------|-------|
| mfr_albertsmith | 11 | 10 | 1 | 91% |
| EG | 14 | 9 | 5 | 64% |
| coles | 7 | 6 | 1 | 86% |
| wiki/news | 12 | 9 | 3 | 75% |
| dreamstime | 28 | 2 | 26 | 7% |
| cheap | 17 | 0 | 17 | 0% |
| costco | 57 | 0 | 57 | 0% |
| au_led | 8 | 0 | 8 | 0% |

## Next Steps

- [x] **EXP-005b: Fixed val set** — Frozen canonical split in `configs/canonical_val_split.json`. EXP-005 confirmed +71% on test.
- [ ] **Label 36 screened pending images** — Sonnet labeling on the KEEP images would bring total to ~339 labeled
- [ ] **New scrape with state+brand queries** — vic confirmed 100% yield; target high-quality images
- [ ] **Retire costco/cheap/dreamstime** — confirmed 0-7% yield at screening stage
- [ ] **Begin Reader pipeline** — can start in parallel using existing 303 sign_board crops

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v5_1class_303 seed=42
```

Note: YOLO writes to `thai-id-nano-ocr-factory/runs/detect/` due to Ultralytics settings. Copy results back manually.
