# EXP-027: Mosaic Augmentation Ablation

## Hypothesis
With v7's bigger targets, mosaic=1.0 will match or beat mosaic=0.5.

## Results

| freeze | mosaic | mAP50 | mAP50-95 | P | R |
|--------|--------|-------|----------|-------|-------|
| 10 | 0.5 | 0.601 | 0.271 | 0.642 | 0.616 |
| 0 | 0.5 | **0.649** | **0.299** | 0.674 | 0.620 |
| 0 | 1.0 | 0.581 | 0.297 | 0.684 | 0.563 |

## Analysis

**Hypothesis rejected.** mosaic=1.0 (0.581) is worse than mosaic=0.5 (0.649) even with v7's bigger targets.

Full mosaic stitches 4 images per frame every batch. Despite v7 targets being 2-3× larger, the extreme distortion still degrades detection quality — particularly recall (0.563 vs 0.620). The model becomes more conservative with higher precision (0.684) but misses more signs.

**mosaic=0.5 remains optimal.** Half mosaic provides scale diversity without overwhelming the learning signal.
