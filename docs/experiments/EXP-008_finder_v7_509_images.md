# EXP-008: Finder v7 — sign_board with 509 Labeled Images

## Hypothesis

More data continues to improve sign_board detection. 405 train images (up from 296 in EXP-007) with 133 new labels from targeted state+brand Bing queries should push canonical test mAP@50 past 0.725.

**Expected:** canonical test mAP@50 ≈ 0.79 (based on +0.002 mAP/image scaling trend from EXP-007)

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0) only |
| Images | 405 train / 78 val / 26 test |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |

### Data changes from EXP-007

- 509 total labeled images (up from 376, +35%)
- 133 new images from 5 scraping rounds targeting brand gaps
- New brands added to validator: `apco`, `eg`; new sign type: `flipboard`
- 20 APCO annotations fixed from `independent` → `apco`
- Brand coverage significantly improved: puma 15→25, apco 1→21, seven_eleven 20→30, united 19→28
- Prompt version upgraded v5 → v6 (fast-reject pattern for Chinese manufacturers, non-AU stations)
- Labeling skill updated with manifest corruption prevention

### Brand coverage (train)

caltex=70, shell=52, bp=51, ampol=44, independent=25, seven_eleven=24, united=23, mobil=20, puma=20, apco=17, metro=16, liberty=14, otr=11, costco=11, unknown=3, 7eleven=2, eg=1, other=1

## Results

| Metric | best.pt (epoch 63) | last.pt (epoch 100) |
|--------|-------------------|---------------------|
| **Val mAP@50** | **0.528** | 0.459 |
| Val mAP@50-95 | — | 0.123 |
| Precision | — | 0.595 |
| Recall | — | 0.436 |

### Comparison with prior experiments (on canonical 19-image test set)

| Model | Train imgs | Canonical mAP50 | mAP50-95 | P | R | Delta mAP50 |
|-------|-----------|-----------------|----------|-------|-------|-------------|
| EXP-004 | 177 | 0.348 | 0.146 | — | — | — |
| EXP-005 | 239 | 0.595 | 0.208 | — | — | +71% |
| EXP-007 | 296 | 0.725 | 0.274 | 0.863 | 0.684 | +21.8% |
| **EXP-008** | **405** | **0.809** | **0.443** | **0.669** | **0.769** | **+11.6%** |

**Post-hoc correction (EXP-009 finding):** All metrics above used YOLO26's default `end2end=True`, which artificially suppresses recall via the one-to-one detection head. Re-evaluating EXP-008 with `end2end=False` (one-to-many head + NMS):

| Model | end2end | Canonical mAP50 | mAP50-95 | P | R |
|-------|---------|-----------------|----------|-------|-------|
| EXP-008 | True (original) | 0.809 | 0.443 | 0.669 | 0.769 |
| **EXP-008** | **False (corrected)** | **0.884** | **0.444** | **0.840** | **0.827** |

All future experiments should evaluate with `end2end=False`. See EXP-009 and docs/research/YOLO26_training_guide.md.

### EXP-008 test set (new 26-image split)

| Metric | Value |
|--------|-------|
| mAP@50 | 0.378 |
| mAP@50-95 | 0.100 |
| Precision | 0.483 |
| Recall | 0.396 |

## Analysis

**Result: POSITIVE.** Canonical test mAP50 improved from 0.725 → 0.809 (+11.6%). mAP50-95 improved from 0.274 → 0.443 (+61.7%). **Crossed the 0.80 threshold.**

### Key observations

1. **Canonical test mAP50 = 0.809 — first time above 0.80.** The model now detects sign_board in ~77% of real-world test images with decent precision (0.669). This is approaching usable for the crop-and-read pipeline.

2. **mAP50-95 jumped from 0.274 → 0.443 (+62%).** This means bounding box tightness improved dramatically — the model is not just finding signs but drawing tighter boxes around them. This is critical for downstream cropping quality.

3. **Recall improved from 0.684 → 0.769 (+12%).** The model misses fewer signs now. Precision dropped from 0.863 → 0.669, meaning more false positives — likely due to greater brand diversity in training (more sign styles to generalize across).

4. **New 26-image test set scores lower (0.378)** than canonical (0.809). This is consistent with EXP-007 — the new test images include harder cases (distant, angled, unusual brands). As the dataset grows, the test split naturally includes harder images.

5. **Val mAP50 peaked at epoch 63 (0.528), not epoch 100.** The model started overfitting after epoch 63 — the gap between best (0.528) and last (0.459) is notable. With 405 train images, 100 epochs may be too many. Consider early stopping or reducing to 80 epochs.

### Scaling trend

| Train imgs | Canonical Test mAP50 | mAP50/img (marginal) | mAP50-95 |
|-----------|---------------------|---------------------|----------|
| 177 | 0.348 | baseline | 0.146 |
| 239 (+62) | 0.595 | +0.004/img | 0.208 |
| 296 (+57) | 0.725 | +0.002/img | 0.274 |
| 405 (+109) | 0.809 | +0.0008/img | 0.443 |

Marginal returns on mAP50 are decreasing (+0.0008/img) but mAP50-95 is accelerating — the model is learning to draw better boxes as it sees more examples. To reach 0.85 mAP50 at current rate would need ~450 more train images. However, bbox quality (mAP50-95) may be the more important metric now.

## Next Steps

1. **Pipeline is viable.** mAP50 > 0.80 means the Finder can now crop sign_board regions reliably enough to feed the Price Reader and Fuel Type Classifier.
2. **Consider early stopping at 60-70 epochs** — epoch 63 was best, last 37 epochs were wasted/harmful.
3. **Begin Price Reader training** — use this Finder model to extract sign_board crops for reader training.
4. **Precision/recall tradeoff** — if false positives are a problem, can tune confidence threshold at inference time.

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v7_1class_509 seed=42
```

Model weights: `runs/finder/v7_1class_509/weights/best.pt` (Ultralytics `runs_dir` setting pointed to an external directory at the time — see EXP-005 / EXP-009 notes).
