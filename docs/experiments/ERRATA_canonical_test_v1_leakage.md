# ERRATA: Canonical Test Set v1 Data Leakage

**Date discovered:** 2026-04-11
**Severity:** Critical — all published canonical mAP50 numbers from EXP-004 through EXP-011 are invalid.

## What Happened

The canonical test set v1 (`configs/canonical_val_split.json`) was created during EXP-005 from a 303-image dataset split with seed=42. At that time, the 19 test images were correctly held out from training.

As the dataset grew (303 → 376 → 509 → 554), `build_finder_dataset.py` re-split ALL images with the same seed=42. Because the stratified split depends on the number of images per brand, adding new images reshuffled the assignments. Images that were in the test split at 303 images migrated to train/val at larger dataset sizes.

**Result:** By the time of EXP-008 (509 images), **14 of 19 canonical test images were in the training set.** The model was evaluated on images it had already memorized.

## Impact on Published Numbers

All "canonical mAP50" metrics in these experiments are **inflated and should not be used for comparison:**

| Experiment | Reported mAP50 | Status |
|-----------|---------------|--------|
| EXP-004 | 0.348 | **COMPROMISED** — leakage level unknown (may be less severe at 249 images) |
| EXP-005 | 0.595 | **COMPROMISED** — leakage level unknown |
| EXP-007 | 0.725 | **COMPROMISED** |
| EXP-008 | 0.884 (e2e=False) | **COMPROMISED** — 14/19 test images in train |
| EXP-009 | 0.740 | **COMPROMISED** |
| EXP-010-A | 0.853 | **COMPROMISED** |
| EXP-010-B | 0.911 | **COMPROMISED** |
| EXP-011 | 0.784 | **COMPROMISED** |

**Note:** The historical experiment documents (EXP-004 through EXP-011) are preserved as-is. They are historical records of what was measured at the time. The numbers are real measurements — they are just not valid measures of generalization because of the train/test overlap.

## Corrected Numbers (Canonical Test v2)

A new clean test set v2 was created from the frozen test split (25 images, zero overlap with any training split). All models re-evaluated:

| Model | Train imgs | Clean mAP50 | Clean mAP50-95 | Clean P | Clean R |
|-------|-----------|-------------|---------------|---------|---------|
| EXP-008 (defaults) | 405 | 0.515 | 0.242 | 0.633 | 0.483 |
| EXP-010-B (freeze+mosaic) | 405 | 0.464 | 0.224 | 0.620 | 0.440 |
| **EXP-012 (reshuffled, +data)** | **440** | **0.596** | **0.286** | **0.683** | **0.680** |
| EXP-012b (frozen split) | 451 | 0.399 | 0.123 | 0.410 | 0.440 |

**Key insights from clean evaluation:**
1. **EXP-012 is actually the best model** (mAP50=0.596), not 10-B
2. **More data helps** — 440 train images beats 405 (0.596 vs 0.515)
3. **The freeze+mosaic recipe hurt** on clean data (0.464 vs 0.515) — it overfit to the leaked test images
4. **True performance is ~0.5-0.6 mAP50**, not 0.9 — significant work remains

## Root Cause

`build_finder_dataset.py` uses `stratified_split(images, seed=42)` which reshuffles ALL images when the dataset size changes. The canonical test set v1 was a static list of filenames, but the actual train/test assignments changed with every dataset rebuild.

## Fix

1. **Canonical test v2** created at `configs/canonical_test_v2.json` — 25 images from the frozen test split
2. **`--freeze-split` flag** added to `build_finder_dataset.py` — preserves val/test assignments when adding data
3. **All future experiments** must use v2 and verify zero overlap before evaluation

## Lesson

Never assume a static test set filename list means static split assignments. When the split function is re-run on a growing dataset, images migrate between splits. The test set must be physically separated or enforced via `--freeze-split`.
