# EXP-015: Higher Resolution (imgsz=1024) with Winning Recipe

## Motivation

EXP-014 confirmed mosaic=0.5 is the sweet spot. The training guide recommends imgsz=1024 for datasets with small targets. Fuel signs vary from 10-80% of frame area — higher resolution preserves detail in distant/small signs that get downscaled to blur at 640px.

## Hypothesis

imgsz=1024 with the 012b recipe (freeze=10, mosaic=0.5, 50 epochs) will improve clean mAP50 from 0.399 to **≥ 0.45** by preserving fine detail in small signs.

**Risk:** 2.56x more pixels = slower training, may need batch=2 to fit in memory.

## Setup

| Parameter | Value | vs 012b |
|-----------|-------|---------|
| **imgsz** | **1024** | was 640 |
| freeze | 10 | same |
| mosaic | 0.5 | same |
| epochs | 50 | same |
| **batch** | **2** | was 4 (halved for memory) |
| Dataset | 561, frozen split, 458 train | same |

## Results

### Canonical Test v2 (25 images, CLEAN, end2end=False)

| Model | imgsz | batch | v2 mAP50 | mAP50-95 | P | R |
|-------|-------|-------|----------|----------|-------|-------|
| **012b (best clean)** | **640** | **4** | **0.399** | **0.123** | 0.410 | 0.440 |
| 015 (1024px) | 1024 | 2 | 0.316 | 0.105 | 0.309 | 0.320 |

Best val epoch: 35 (mAP50=0.308). Training time: ~46 min (50 epochs).

## Analysis

**Hypothesis rejected.** Higher resolution hurt (0.399 → 0.316). Two likely causes:
1. **Halved batch size** (4→2) reduced gradient diversity per step, destabilizing training
2. **More parameters active per image** increases overfitting risk on small datasets

The training guide recommends imgsz=1024 for datasets with many small targets AND sufficient data (1000+). At 458 images, the batch size tradeoff isn't worth it.

## Next Steps

- 012b (freeze=10, mosaic=0.5, imgsz=640, batch=4, 50ep) remains the best clean recipe
- Next: try 2-class (sign_board + fuel_price) for 3.2x more supervision per image
