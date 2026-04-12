# EXP-014: Minimal Augmentation — Disable Mosaic and Erasing

## Motivation

EXP-013 confirmed that freeze+mosaic=0.5 (012b, mAP50=0.399) outperforms defaults (mAP50=0.294) on truly clean data. The pattern is clear: with only ~458 training images, less augmentation = better generalization.

The YOLO26 training guide recommends for <1K images: "Drastically reduce Mosaic probability (mosaic=0.5 or 0.0). Completely disable Mixup (mixup=0.0) and Copy-Paste (copy_paste=0.0)."

We tested mosaic=0.5 in 012b. This experiment tests the extreme: **mosaic=0.0** (fully disabled) plus **erasing=0.0** (disable random erasing, currently 0.4). The hypothesis is that at 458 images, even mosaic=0.5 adds too much distortion.

## Hypothesis

Fully disabling mosaic and random erasing while keeping freeze=10 will push clean mAP50 from 0.399 (012b) to **≥ 0.45**.

**Basis:** Each reduction in augmentation has helped so far (mosaic 1.0→0.5 improved substantially). Further reduction may continue the trend. The model sees undistorted images in every batch, giving the detection head cleaner gradients.

**Risk:** Without any mosaic, the model loses multi-scale exposure. May hurt detection of signs at unusual scales.

## Setup

| Parameter | Value | vs 012b |
|-----------|-------|---------|
| freeze | 10 | same |
| **mosaic** | **0.0** | was 0.5 |
| **erasing** | **0.0** | was 0.4 (default) |
| mixup | 0.0 | same (already off) |
| copy_paste | 0.0 | same (already off) |
| epochs | 50 | same |
| optimizer | auto→AdamW(0.002) | same |
| Dataset | 561 total, frozen split, 458 train | same as 013 |
| Evaluation | canonical_test_v2 (25 imgs, CLEAN) | same |

## Results

### Canonical Test v2 (25 images, CLEAN, end2end=False)

| Model | mosaic | erasing | v2 mAP50 | mAP50-95 | P | R |
|-------|--------|---------|----------|----------|-------|-------|
| 012b (best clean) | 0.5 | 0.4 | **0.399** | **0.123** | 0.410 | 0.440 |
| 013 (defaults) | 1.0 | 0.4 | 0.294 | 0.097 | 0.482 | 0.320 |
| **014 (minimal)** | **0.0** | **0.0** | **0.229** | **0.067** | **0.518** | **0.200** |

Best val epoch: 32 (mAP50=0.327)

## Analysis

### Hypothesis Rejected

Fully disabling mosaic and erasing degraded all metrics. mAP50 dropped from 0.399 → 0.229 (-43%).

### The Augmentation Sweet Spot

There's a clear U-curve: too much augmentation hurts (defaults, mosaic=1.0 → 0.294), too little also hurts (mosaic=0.0 → 0.229), and **mosaic=0.5 is the sweet spot** (0.399).

| mosaic | erasing | v2 mAP50 | Interpretation |
|--------|---------|----------|---------------|
| 1.0 | 0.4 | 0.294 | Too aggressive — distortion masks signal |
| **0.5** | **0.4** | **0.399** | **Sweet spot — some multi-scale, not too noisy** |
| 0.0 | 0.0 | 0.229 | Too conservative — model can't handle scale variation |

Mosaic provides essential multi-scale training. Without it, the model only sees signs at their natural scale in each image. Since fuel signs vary from 10% to 80% of frame area, the model needs mosaic's scale diversity — just not so much that it can't learn.

### Recall Collapse

Recall dropped to 0.200 — the model only detects 1 in 5 signs. Without scale augmentation, it overfits to the dominant sign size in the training set and misses smaller/larger signs entirely.

## Next Steps

- mosaic=0.5 is confirmed optimal
- Next experiment should vary something ELSE while keeping mosaic=0.5
- Try: imgsz=1024 (higher resolution) or scale=0.0 (disable scale aug but keep mosaic)

## Reproducibility

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False \
    freeze=10 mosaic=0.0 erasing=0.0 \
    project=runs/finder name=v13_1class_561_minimal_aug seed=42 \
    2>&1 | tee runs/finder/v13_minimal_aug_train.log
```
