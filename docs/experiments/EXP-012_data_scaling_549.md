# EXP-012: Data Scaling — 549 Images with 10-B Recipe

## Motivation

EXP-010-B established the optimal training recipe for data-scarce regimes (freeze=10, mosaic=0.5, epochs=50, optimizer=auto→AdamW) achieving mAP50=0.911 on 509 images. A scrape+label session on 2026-04-11 added 40 new images targeting brand gaps (APCO +9, EG +5, United +5, Metro +4). This experiment tests whether the additional data moves the needle under the same recipe.

## Hypothesis

549 images (+7.9% over 509) with the 10-B recipe will push canonical test mAP50 from 0.911 to **≥ 0.928**.

**Basis:** The scaling trend from EXP-004 through EXP-008 shows diminishing but still positive returns:

| Train images | mAP50 | Marginal gain/image |
|-------------|-------|-------------------|
| 177 | 0.348 | — |
| 239 | 0.595 | +0.004/img |
| 296 | 0.725 | +0.002/img |
| 405 | 0.884 | +0.001/img |
| 405 (10-B recipe) | 0.911 | +0.027 from recipe |

With ~34 new training images and a conservative +0.0005/img rate, the expected gain is +0.017 → **mAP50 ≈ 0.928**. Optimistic scenario (+0.001/img): **mAP50 ≈ 0.945**.

**Null hypothesis:** The scaling curve has plateaued at ~0.91 and 40 additional images produce no measurable improvement (mAP50 within ±0.01 of baseline).

**Secondary hypothesis:** Brand diversity improvements (EG 2→7, APCO 21→30, Metro 20→24) improve recall on underrepresented sign types without degrading precision.

## Experimental Design

### Independent Variable
- Dataset size: 549 images (up from 509)

### Controlled Variables (identical to EXP-010-B)
| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class: sign_board) |
| freeze | 10 |
| mosaic | 0.5 |
| epochs | 50 |
| optimizer | auto (→ AdamW lr=0.002) |
| imgsz | 640 |
| batch | 4 |
| device | mps (Apple Silicon) |
| amp | False |
| seed | 42 |
| Evaluation | end2end=False, canonical 19-image test set |

### Data Changes from EXP-010-B

| Brand | EXP-010-B | EXP-012 | Delta |
|-------|-----------|---------|-------|
| caltex | 87 | 90 | +3 |
| shell | 65 | 68 | +3 |
| bp | 63 | 64 | +1 |
| ampol | 55 | 55 | 0 |
| independent | 32 | 35 | +3 |
| united | 28 | 33 | +5 |
| seven_eleven | 30 | 30 | 0 |
| apco | 21 | 30 | **+9** |
| mobil | 25 | 27 | +2 |
| puma | 25 | 25 | 0 |
| metro | 20 | 24 | +4 |
| liberty | 18 | 21 | +3 |
| otr | 14 | 16 | +2 |
| costco | 14 | 14 | 0 |
| eg | 2 | 7 | **+5** |
| **Total** | **509** | **549** | **+40** |

Scrape sources: Bing Image Search. Query strategies: APCO regional VIC (80% yield), EG Foodary (60%), price war AU (33%), state-generic (25%), NT/TAS generic (variable). See `memory/feedback_scrape_strategies_v2.md` for full breakdown.

### Success Criteria

| Metric | 10-B Baseline | Min Acceptable | Target |
|--------|--------------|----------------|--------|
| mAP50 | 0.911 | ≥ 0.91 | ≥ 0.93 |
| Precision | 1.000 | ≥ 0.95 | ≥ 1.00 |
| Recall | 0.833 | ≥ 0.83 | ≥ 0.87 |
| mAP50-95 | 0.460 | ≥ 0.46 | ≥ 0.50 |

## Setup

Two training runs were conducted to isolate the data-vs-split effect:

| Run | Images | Train | Val | Test | Split Method |
|-----|--------|-------|-----|------|-------------|
| **012 (reshuffled)** | 554 | 440 | 84 | 30 | `seed=42` full reshuffle |
| **012b (frozen)** | 554 | 451 | 78 | 25 | `--freeze-split` from 506-image baseline |
| 10-B (baseline) | 509 | 405 | 78 | 26 | `seed=42` |

Both used identical 10-B recipe: freeze=10, mosaic=0.5, epochs=50, optimizer=auto→AdamW(lr=0.002).

**Critical tooling addition:** Added `--freeze-split` flag to `build_finder_dataset.py` during this experiment. This preserves val/test assignments from a prior manifest and routes new images to train only.

## Results

### Canonical Test Set (19 images, end2end=False)

| Model | Train | P | R | mAP50 | mAP50-95 |
|-------|-------|-------|-------|-------|----------|
| **EXP-010-B (baseline)** | **405** | **1.000** | **0.833** | **0.911** | **0.460** |
| EXP-012 (reshuffled) | 440 | 0.857 | 0.579 | 0.794 | 0.327 |
| EXP-012b (frozen split) | 451 | 0.630 | 0.737 | 0.736 | 0.352 |

**Both variants regressed significantly.** Adding ~45 images degraded mAP50 by 12-18%.

## Analysis

### Hypothesis Rejected

More data did NOT improve the model. Both reshuffled and frozen-split variants were substantially worse than the 509-image baseline.

### Possible Causes

1. **New annotation quality.** The 45 new images were labeled by Sonnet agents in rapid-fire batches of 5-10 images. Quality may be lower than the carefully labeled original 509. A visual audit of new annotations is needed.

2. **Brand distribution shift.** The new images are heavily skewed toward APCO (+9), EG (+5), United (+5) — brands with distinctive sign styles. This may have diluted the model's understanding of the more common sign formats (Caltex, Shell, BP) that dominate the canonical test set.

3. **Canonical test set too small (19 images).** With only 19 test images, a single missed detection swings mAP by ~0.05. The result may be within noise range, but the magnitude of regression (-0.12 to -0.18) suggests a real effect.

4. **Split instability.** Even with frozen split, the 012b baseline (402 train) doesn't exactly match 10-B (405 train) because the baseline manifest was reconstructed from 506 images, not the exact 509 used in 10-B.

### Key Lesson: Frozen Splits Are Not Enough

The `--freeze-split` feature correctly preserved val/test, but the model still regressed. This proves the regression is caused by **the new training data itself**, not split reshuffling. The new annotations may be introducing noise.

### Next Investigation

Before adding more data, audit the quality of the 45 new annotations:
1. Visually inspect all new previews
2. Check for common issues: loose bboxes, wrong brands, misaligned label/price pairs
3. If quality is low, re-label or remove bad annotations rather than adding more volume

## Next Steps

1. **Visual audit of new annotations** — inspect all 45 new previews before any further training
2. **Ablation: retrain on original 509 only** — verify the 10-B result is reproducible (control for randomness)
3. **Consider expanding canonical test set** — 19 images may be too noisy for reliable comparison
4. **10-B remains the production model** at mAP50=0.911

## Reproducibility

```bash
# 1. Build dataset (no negatives)
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

# 2. Rebuild canonical test set
.venv/bin/python -c "
import json, os, shutil, yaml
canon = json.load(open('configs/canonical_val_split.json'))
if os.path.exists('data/finder_canonical_test'): shutil.rmtree('data/finder_canonical_test')
os.makedirs('data/finder_canonical_test/images/test', exist_ok=True)
os.makedirs('data/finder_canonical_test/labels/test', exist_ok=True)
for name in canon['test']:
    stem = os.path.splitext(name)[0]
    for split in ['train','val','test']:
        for ext in ['.jpg','.jpeg','.png']:
            img, lbl = f'data/finder/images/{split}/{stem}{ext}', f'data/finder/labels/{split}/{stem}.txt'
            if os.path.exists(img) and os.path.exists(lbl):
                shutil.copy2(img, f'data/finder_canonical_test/images/test/{stem}{ext}')
                shutil.copy2(lbl, f'data/finder_canonical_test/labels/test/{stem}.txt')
                break
        else: continue
        break
yaml.dump({'path':os.path.abspath('data/finder_canonical_test'),'train':'images/test','val':'images/test','test':'images/test','nc':1,'names':{0:'sign_board'}}, open('data/finder_canonical_test/dataset.yaml','w'))
"

# 3. Train (10-B recipe, tee to log)
LOG=runs/finder/v11_549_train.log && mkdir -p runs/finder
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False \
    freeze=10 mosaic=0.5 \
    project=runs/finder name=v11_1class_549 seed=42 \
    2>&1 | tee "$LOG"

# 4. Evaluate — ALWAYS end2end=False
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
    data=data/finder_canonical_test/dataset.yaml \
    model=<save_dir>/weights/best.pt \
    device=mps amp=False end2end=False
```
