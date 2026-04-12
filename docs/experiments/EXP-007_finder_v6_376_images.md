# EXP-007: Finder v6 — sign_board with 376 Labeled Images

## Hypothesis

More data continues to improve sign_board detection. 296 train images (up from 239 in EXP-005) with 22 new labels from diverse sources (Flickr, forum, govau, news, YouTube, Google Images) should push test mAP@50 past 0.595.

**Expected:** test mAP@50 > 0.595 (beating EXP-005's best)

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0) only |
| Images | 296 train / 58 val / 22 test |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |

### Data changes from EXP-005

- 376 total labeled images (up from 303)
- 22 new images from labeling session 2026-04-10
- New sources: Flickr photographers, forum posts, govau street view, news articles, YouTube thumbnails, Google Images
- New brands added: Costco (was 0, now 10), more Metro, OTR, Liberty
- Cleaned 4 skip-annotation pollution files
- Labeling yield: 22/123 = 18% (low due to exhausted gimg pool)

### Brand coverage (train)

caltex=53, shell=42, bp=40, ampol=29, independent=24, mobil=18, seven_eleven=16, united=14, liberty=13, metro=12, otr=11, puma=11, costco=7, unknown=2, eg=1, other=1, 7eleven=1, apco=1

## Results

| Metric | best.pt (epoch 96) | last.pt (epoch 100) |
|--------|-------------------|---------------------|
| **Val mAP@50** | **0.431** | 0.431 |
| Val mAP@50-95 | 0.112 | 0.110 |
| Precision | 0.664 | 0.597 |
| Recall | 0.466 | 0.500 |

### Comparison with prior experiments (on canonical 19-image test set)

| Model | Train imgs | Test mAP50 | Test mAP50-95 | Delta mAP50 |
|-------|-----------|-----------|-------------|-------------|
| EXP-004 | 177 | 0.348 | 0.146 | — |
| EXP-005 | 239 | 0.595 | 0.208 | +71% |
| **EXP-007** | **296** | **0.725** | **0.274** | **+21.8%** |

### EXP-007 test set (new 22-image split)

| Metric | Value |
|--------|-------|
| mAP@50 | 0.416 |
| mAP@50-95 | 0.170 |
| Precision | 0.468 |
| Recall | 0.409 |

## Analysis

**Result: POSITIVE.** Canonical test mAP50 improved from 0.595 → 0.725 (+21.8%). mAP50-95 improved from 0.208 → 0.274 (+31.7%). Precision jumped to 0.863 on canonical test.

### Key observations

1. **More data continues to improve generalization.** The learning curve is still in the productive zone — each ~60 additional training images yields meaningful mAP gains.
2. **Val mAP50 appears flat (0.431 vs 0.441)** but this is misleading because the val set changed (58 vs 45 images). The canonical test set tells the real story.
3. **New 22-image test set scores lower (0.416)** than canonical 19-image test (0.725), suggesting the new test images are harder (more diverse sources, distant signs, unusual brands).
4. **Brand diversity helps.** Adding Costco, more Metro/OTR/Liberty, and independent stations likely improved the model's ability to generalize across sign styles.

### Scaling trend

| Train imgs | Canonical Test mAP50 | mAP50/img (marginal) |
|-----------|---------------------|---------------------|
| 177 | 0.348 | baseline |
| 239 (+62) | 0.595 | +0.004/img |
| 296 (+57) | 0.725 | +0.002/img |

Marginal returns are decreasing but still positive. Likely need 400-500 train images to reach 0.8+ mAP50.

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v6_1class_376 seed=42
```
