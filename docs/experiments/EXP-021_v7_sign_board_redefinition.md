# EXP-021: v7 sign_board Redefinition — Training Test

## Hypothesis

155 images with v7 sign_board labels (full physical panel) will achieve **comparable or better mAP50** than EXP-019's 483 images with old labels (fuel rows only), despite having 3x fewer images.

**Basis:** The v7 target is 2-3x larger, structurally consistent, and unambiguous. The model should learn faster with clearer supervision signal, even with less data.

**Baseline:** EXP-019 = mAP50 0.517 on canonical test v2 (483 train, old labels)

**Caveat:** The v2 test set has mixed ground truth — 10/25 images are v7, 15/25 are old. mAP50-95 will be affected by this mismatch (predicted boxes won't match old tight labels at high IoU). mAP50 should still be meaningful since 50% IoU is lenient enough to match both definitions.

## Setup

| Parameter | Value |
|-----------|-------|
| Dataset | 154 v7 images: 123 train / 21 val / 10 test |
| sign_board definition | v7 (full physical panel) |
| Recipe | freeze=10, mosaic=0.5, 50 epochs, optimizer=auto |
| Evaluation | canonical_test_v2 (25 images, 0 leakage, mixed v7/old labels) |

## Results

*Pending training...*
