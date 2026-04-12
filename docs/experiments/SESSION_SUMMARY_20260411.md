# Session Summary: 2026-04-11 — The Day We Found the Leakage

## Overview

This was the most consequential session in the project. We ran 10 experiments (EXP-009 through EXP-018), discovered a critical data leakage bug that invalidated all prior metrics, established a clean evaluation protocol, and mapped the true state of the Finder model.

## Timeline

| Time | Event | Result |
|------|-------|--------|
| Start | EXP-009: Hard negatives (44 background images) | **Failed** — negatives hurt at this scale |
| +1h | EXP-010-A/B: Data-scarce recipe from YOLO26 training guide | "0.911 mAP50" (believed to be best) |
| +2h | EXP-011: SGD with nano lr schedule | Failed — AdamW better for small datasets |
| +3h | Scrape+label loop: 3 rounds, 40 new images (509→556) | 34 labeled from 510 scraped |
| +4h | EXP-012/012b: Retrain with more data | "Regression" — 0.911→0.794 |
| +5h | **DISCOVERY: Data leakage** in canonical test v1 | 14/19 test images in training |
| +5.5h | Created canonical test v2 (25 clean images) | True best: 012b = **0.399 mAP50** |
| +6h | EXP-013: Defaults on clean split | 0.294 — freeze+mosaic recipe confirmed better |
| +7h | EXP-014: mosaic=0.0 (minimal aug) | 0.229 — too conservative |
| +8h | EXP-015: imgsz=1024 (higher res) | 0.316 — batch=2 too small |
| +9h | EXP-016: 2-class (sign_board + fuel_price) | 0.380 — didn't beat 1-class |
| +10h | EXP-017: freeze=5 (partial unfreeze) | 0.387 — close but no improvement |
| +11h | EXP-018: freeze=10, 100 epochs | 0.340 — 100ep overfits, 50ep confirmed better |

## Clean v2 Scoreboard

All metrics on canonical test v2 (25 images, verified 0 leakage, end2end=False):

| Rank | EXP | Key Change | Train | v2 mAP50 | P | R |
|------|-----|-----------|-------|----------|-------|-------|
| **1** | **012b** | **freeze=10, mosaic=0.5, 50ep** | **451** | **0.399** | **0.410** | **0.440** |
| 2 | 017 | freeze=5 | 458 | 0.387 | 0.664 | 0.316 |
| 3 | 016 | 2-class | 458 | 0.380 | 0.464 | 0.400 |
| 4 | 015 | imgsz=1024 | 458 | 0.316 | 0.309 | 0.320 |
| 5 | 013 | defaults | 458 | 0.294 | 0.482 | 0.320 |
| 6 | 014 | mosaic=0.0 | 458 | 0.229 | 0.518 | 0.200 |

## Key Findings

### 1. Data Leakage Invalidated All Prior Metrics

The canonical test v1 (19 images from EXP-005) was created when the dataset had 303 images. As images were added and the dataset re-split with seed=42, 14/19 test images migrated to the training set. All reported mAP50 numbers (0.348 through 0.911) were measuring memorization, not generalization.

**Impact:** The "0.911 best model" was an illusion. True performance on unseen images is ~0.40 mAP50.

### 2. The Freeze+Mosaic Recipe IS Better (On Clean Data)

| Setting | Clean mAP50 |
|---------|------------|
| freeze=10, mosaic=0.5 | **0.399** |
| freeze=5, mosaic=0.5 | 0.387 |
| defaults (no freeze) | 0.294 |
| mosaic=0.0 | 0.229 |

The pattern is consistent: more frozen backbone layers + moderate augmentation generalizes best on small datasets. The COCO pretrained backbone features are more valuable than task-specific fine-tuning when you only have ~450 training images.

### 3. Augmentation Has a Sweet Spot

mosaic=0.5 is optimal. mosaic=1.0 (too aggressive) and mosaic=0.0 (too conservative) both hurt. The model needs SOME scale diversity from mosaic but not so much that it can't learn patterns.

### 4. Hyperparameter Tuning Has Plateaued

Six experiments (013-018) tested different hyperparameters on the same ~458 training images. The range was 0.229–0.399 mAP50 — a 1.7x spread. But the best (012b, 0.399) is only marginally above the second-best (017, 0.387). Further tuning is unlikely to break past 0.40 without more data.

### 5. Scraping Is Hitting Diminishing Returns

510 scraped → 104 after dedup → 34 labeled (6.7% end-to-end yield). APCO regional VIC is the last high-yield source. OTR and Costco are essentially impossible to find on Bing.

## Lessons Learned

1. **Test set integrity is non-negotiable.** Always use `--freeze-split` and verify 0 leakage before training.
2. **Never trust growing datasets with static test set filenames.** The split function reshuffles everything.
3. **Clean evaluation reveals the truth.** "Regressions" were often the model being honest for the first time.
4. **Negative results are valuable.** EXP-009 (negatives), EXP-011 (SGD), EXP-014 (no mosaic), EXP-015 (1024px), EXP-016 (2-class) all failed — each failure narrows the search space.
5. **Observable training prevents silent failures.** Always use `tee` for training output.

## Where We Stand (Updated 2026-04-12)

- **Best model:** EXP-021c (mAP50=**0.770**, R=0.880 on clean v2)
- **Best recipe:** freeze=10, mosaic=0.5, 50 epochs, optimizer=auto
- **Dataset:** 596 labeled images, all expanded to v7 sign_board (physical panel)
- **Key breakthrough:** v7 sign_board redefinition (+103% mAP50 from 0.379 → 0.770)
- **Bottleneck shifted:** Now data volume again (need 800+ for mAP50 > 0.85)

### Late Session Additions (2026-04-12)

| Time | Event | Result |
|------|-------|--------|
| +12h | EXP-019: +25 new images | **0.517** — first clean data scaling win |
| +13h | EXP-020: +15 more images | 0.357 — regression from bad annotations |
| +14h | v7 sign_board redefinition | Architecture overhaul |
| +15h | EXP-022: Haiku vs Sonnet screening study | Sonnet wins 93% vs 77%, same cost |
| +16h | v7 relabeling (155 Sonnet, batches 3-34) | 155/596 converted |
| +17h | Programmatic expansion (344 auto-merge + 97 heuristic) | Free, instant |
| +18h | EXP-021c: All expanded v7 | **mAP50=0.770, R=0.880** — best ever |

## Infrastructure Improvements Made

1. `--freeze-split` flag in `build_finder_dataset.py`
2. `image_manifest.json` saved per build for reproducibility
3. `canonical_test_v2.json` with 25 verified clean images
4. `ERRATA_canonical_test_v1_leakage.md` documenting the issue
5. ml-researcher skill updated with v2 protocol
6. Scrape-dispatch skill updated with winning/losing strategies
7. Memory records for end2end=False, observable training, leakage prevention
