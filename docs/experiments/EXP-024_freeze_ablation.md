# EXP-024: Freeze Ablation on v7 Labels

## Hypothesis
With v7 sign_board labels (bigger, structural targets), freeze=0 (all layers trainable) will outperform freeze=10, achieving mAP50 ≥ 0.63.

## Results

| Experiment | freeze | mAP50 | mAP50-95 | P | R | vs baseline |
|-----------|--------|-------|----------|-------|-------|------------|
| 023 mean (baseline) | 10 | 0.601 | 0.271 | 0.642 | 0.616 | — |
| **024a** | **0** | **0.649** | **0.299** | **0.674** | **0.620** | **+0.048 (+8%)** |

## Analysis

**Hypothesis confirmed.** freeze=0 achieves 0.649, which is +0.048 above baseline — more than 3× the measured std (0.015). This is a statistically significant improvement.

With v7's bigger, structural targets, the backbone benefits from learning fuel-sign-specific features. The COCO pretrained features (edges, textures, generic shapes) are useful but not optimal for detecting rectangular sign panels with LED digits and brand logos.

**freeze=0 is the new recommended setting for v7 labels.** This reverses the finding from earlier experiments (EXP-013 vs 012b) where freeze=10 was better — that was on old "fuel rows only" labels where the targets were too small for the backbone to learn meaningful features.

## Updated Recipe
```
freeze=0, mosaic=0.5, 50 epochs, optimizer=auto (AdamW)
```
