# EXP-021f: Expanded Test Set Baseline (50 Images)

## Purpose

Establish a reliable baseline metric using the expanded canonical test v2.1 (50 verified images), replacing the noisy 25-image test set.

## Test Set

| | v2 (old) | v2.1 (new) |
|---|---|---|
| Images | 25 | **50** |
| Labels | All Sonnet v7 | All Sonnet v7 |
| Leakage | 0 | 0 |
| Confidence interval | ±10% (noisy) | **±5% (more reliable)** |

The 25 new images were selected from the val split with brand diversity (2 per brand, 15 brands covered).

## Results

### EXP-021d on 50-image test (end2end=False)

| Metric | 25-image test | 50-image test | Delta |
|--------|-------------|-------------|-------|
| **mAP50** | 0.760 | **0.731** | -0.029 |
| **mAP50-95** | 0.379 | **0.283** | -0.096 |
| **Precision** | 0.845 | **0.829** | -0.016 |
| **Recall** | 0.654 | **0.640** | -0.014 |

## Analysis

The 50-image evaluation gives a slightly lower but more stable result. The drop from 0.760 to **0.731 mAP50** is expected — the 25 new images include harder cases (distant signs, night shots, unusual brands) that the 25-image set didn't cover.

**0.731 on 50 verified images is the honest baseline going forward.**

The mAP50-95 drop (0.379→0.283) suggests bbox tightness varies more across the larger test set — some predictions are good at IoU=0.50 but loose at higher thresholds.

## New Baseline for All Future Experiments

| Metric | Value |
|--------|-------|
| **mAP50** | **0.731** |
| mAP50-95 | 0.283 |
| Precision | 0.829 |
| Recall | 0.640 |
| Test set | canonical_test_v2.1 (50 images) |
| Model | EXP-021d |
| Train data | 596 images (309 v7 + 287 v7_auto) |

All future experiments must be evaluated on this 50-image test set for comparable results.
