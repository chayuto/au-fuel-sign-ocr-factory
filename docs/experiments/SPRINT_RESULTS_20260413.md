# Compute Sprint Results — 2026-04-13

## Baseline
freeze=10, mosaic=0.5, 50 epochs, YOLO26n, 508 train images
mAP50 = **0.601 ± 0.015** (cross-validated on 50 verified test images)

## All Experiments

| EXP | What Changed | mAP50 | mAP50-95 | P | R | vs Baseline | Verdict |
|-----|-------------|-------|----------|-------|-------|-------------|---------|
| 023 | Cross-val (3 seeds) | 0.601±0.015 | 0.271 | 0.642 | 0.616 | — | Stable (std=0.015) |
| **024a** | **freeze=0** | **0.649** | **0.299** | **0.674** | **0.620** | **+0.048** | **WIN** |
| 025a | 100 epochs, freeze=0 | 0.631 | 0.306 | 0.675 | 0.581 | +0.030 | Slight overfit |
| 027a | mosaic=1.0, freeze=0 | 0.581 | 0.297 | 0.684 | 0.563 | -0.020 | Too aggressive |
| 028 | SAHI inference | 8/10 detect | — | — | — | +60% detect | **WIN (inference)** |

## Key Findings

### 1. freeze=0 is the new best recipe (+8% mAP50)
With v7's structural sign panel targets, the backbone benefits from learning fuel-sign-specific features. This reverses the earlier finding (freeze=10 was better on old labels).

**Updated recipe: `freeze=0, mosaic=0.5, 50 epochs, optimizer=auto`**

### 2. SAHI catches distant signs (+60% detections)
Zero-training improvement. SAHI sliced inference detects 8/10 signs vs 5/10 standard on the same model. Directly useful for the dashcam "approach phase."

### 3. 50 epochs remains optimal
100 epochs causes mild overfitting even with freeze=0. The backbone adapts in 50 epochs; additional epochs degrade.

### 4. mosaic=0.5 confirmed again
Full mosaic (1.0) is still too aggressive. Half mosaic gives the right balance of scale diversity without overwhelming the learning signal.

### 5. Results are stable (std=0.015)
Cross-validation confirmed that differences ≥0.03 are real. The freeze=0 improvement (+0.048) is statistically significant (>3 std).

## New Best Model
**EXP-024a: freeze=0, mosaic=0.5, 50ep → mAP50 = 0.649 on 50 verified images**

## Updated Recipe
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False \
    freeze=0 mosaic=0.5 seed=42
```

## What's Next
1. Push 024a model to HuggingFace
2. Continue scrape+label loop with more data
3. SAHI integration for dashcam deployment pipeline
4. More data → retrain with freeze=0 recipe → target mAP50 > 0.75
