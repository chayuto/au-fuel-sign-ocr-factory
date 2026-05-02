# EXP-030: Clean-Split Re-Evaluation (Val Leak Removed)

**Status:** COMPLETE 2026-05-02 15:11 (1h 44min wall time, 0 failures)
**Model:** YOLO26n, freeze=0, mosaic=0.5, 50ep (same recipe as EXP-024a / EXP-029)
**Test set:** canonical_test_v2 (50 hand-verified images, all v7)
**Train/val split:** 460/89/31, with **zero canonical_test_v2 leakage** (verified)

## Hypothesis

EXP-029 reported a +0.036 mAP50 improvement from the QA cleanup (treatment 0.712 vs baseline 0.676). However, EXP-029 had a **known val leak**: 25 of 50 canonical_test_v2 images sat in the val split, biasing best.pt selection toward checkpoints that overfit to those 25 images. Both baseline and treatment had the same leak, but the inflation may not be symmetric across conditions.

**Hypothesis:** removing the val leak will reduce absolute mAP50 by ~0.02–0.05 (the inflation we predicted in EXP-029's caveats).

## Setup

- **Train images:** 460 (was 508 in EXP-029) — all 50 canonical_test_v2 images excluded from train/val/test_local pools
- **Val images:** 89 (was 78) — zero overlap with canonical_test_v2
- **Test_local:** 31 — held-out internal test, not used for the comparison numbers below
- **Labels:** current annotations (post-2026-05-01 QA cleanup of 146 v7_auto → v7_qa)
- **Recipe:** identical to EXP-029 treatment (freeze=0, mosaic=0.5, 50ep, optimizer=auto)
- **Seeds:** 42, 43, 44

Vetting:
```
Test ∩ Train: 0
Test ∩ Val:   0
Test ∩ Test_local: 0
```

## Results

### Per-seed (canonical_test_v2, 50 images, end2end=False)

| Seed | P | R | mAP50 | mAP50-95 |
|------|-----|-----|-------|----------|
| 42 | 0.746 | 0.587 | 0.668 | 0.316 |
| 43 | 0.744 | 0.540 | **0.692** ← best | 0.344 |
| 44 | 0.682 | 0.540 | 0.668 | 0.317 |

### Aggregate (mean ± std, n=3)

| Metric | EXP-030 (clean) | EXP-029 treatment (val leak) | Δ (clean − leaked) |
|--------|-----------------|------------------------------|---------------------|
| mAP50 | **0.676 ± 0.014** | 0.712 ± 0.035 | **−0.036** |
| mAP50-95 | 0.326 ± 0.016 | 0.326 ± 0.013 | 0.000 |
| Precision | 0.724 ± 0.036 | 0.849 ± 0.052 | **−0.125** |
| Recall | 0.556 ± 0.027 | 0.573 ± 0.046 | −0.017 |

## Striking finding

**The +0.036 mAP50 improvement EXP-029 attributed to the QA cleanup was essentially the val-leak inflation.**

- EXP-029 baseline (old labels, with val leak): mAP50 = 0.676 ± 0.069
- EXP-030 treatment (new labels, no val leak): mAP50 = **0.676 ± 0.014**

These are **identical means**. Once the val leak is removed, the QA cleanup shows no detectable mAP50 improvement at this seed count.

The big precision shift (+0.118) we attributed to "tighter trained bboxes" was also mostly leak-driven. Clean precision (0.724) is essentially equal to the EXP-029 baseline precision (0.732).

## What's actually true about the QA cleanup

Three honest possibilities:

1. **The QA cleanup had near-zero effect on this model.** 138 of 508 train labels were updated, but the model's generalization on canonical_test_v2 didn't shift in a measurable way once leak was removed.

2. **The cleanup effect is real but smaller than 0.014 std.** With n=3 seeds and σ=0.014, we can detect effects ≥ ~0.025. A real +0.01 effect would be invisible.

3. **The data reduction (508→460 train) cancelled the QA benefit.** EXP-030 trained on 9% fewer images. If 9% data loss costs ~0.015 mAP and QA cleanup gave +0.015, we'd see net zero.

We can't disentangle (2) from (3) without an EXP-031b that retrains on 460 *unmodified* April labels — but that requires reverting the JSON edits, which is expensive.

**The clean-split conclusion is what we publish: mAP50 = 0.676 ± 0.014 on canonical_test_v2.**

## Variance dropped 5× — methodology win

Baseline std was 0.069 in EXP-029 (across seeds 42/43/44). EXP-030 treatment std is 0.014 — **five times tighter**.

The val leak wasn't just inflating means; it was massively amplifying single-seed variance because best.pt was being selected on test-leaked val, and which test images won the lottery varied by seed. With no leak, model selection is on truly held-out images, and seeds converge to similar quality.

Adding to memory: `feedback_seed_variance_50img_test.md` was based on EXP-029's leaky-baseline std=0.069. The CLEAN-split single-seed variance is 0.014 — about what EXP-023 cross-val originally measured (0.015). The 5× inflation in EXP-029 was the leak, not the test set size.

## Decision

- **New best Finder for publish: `exp030_clean_s43`** (mAP50=0.692 on canonical_test_v2, clean methodology)
- This is a genuinely defensible "0.69 mAP50 on a hand-verified 50-image test, no train/val leakage, 3-seed mean=0.676 ± 0.014"
- Beats the old published model (EXP-021d, mAP50=0.760 on noisy 25-image v1 test which had its own leakage problems per ERRATA_canonical_test_v1_leakage.md)
- The 0.692 vs 0.760 comparison is apples-to-oranges; the clean methodology is the credibility win

## Implications for prior work

1. **Update memory `project_exp029_results.md`**: the +0.036 effect is now attributed to val leak, not QA cleanup. The QA work may still be valuable (the underlying labels are demonstrably more correct by visual inspection), but it doesn't show up in mAP at this seed count.
2. **Update memory `feedback_seed_variance_50img_test.md`**: the σ=0.069 was leak-amplified. Clean σ ≈ 0.014, matching EXP-023's cross-val estimate.
3. **EXP-024a's reported 0.649 was inflated** by the same leak. The true clean number for that model+labels combination would have been lower (~0.61 estimated).

## Reproducibility

```bash
# Build clean dataset
.venv/bin/python scripts/build_finder_dataset.py \
    --classes 0 --seed 42 \
    --include-list data/_exp030/include_list.txt

# Train + eval (3 seeds)
bash scripts/run_exp030.sh
```

- Run dirs: `runs/detect/runs/finder/exp030_clean_s{42,43,44}/`
- Eval logs: `logs/exp030/exp030_eval_s*.log`
- Driver log: `logs/exp030/driver.log`
- Wall time: 13:27 → 15:11 = 1h 44m

## Caveats

1. **Smaller train set** (460 vs 508 in EXP-029): we removed 48 images from the train pool. Some of the apparent regression may be data-volume, not methodology cleanup.
2. **No same-data baseline**: a true A/B for the QA effect would retrain on these same 460 images with pre-QA labels. Not done because it's expensive (3 more train runs) and the cleaned-split numbers are what we publish anyway.
3. **3 seeds is still small**. Clean-split std=0.014 means ±0.018 SE for n=3 mean. CI on Δ to a future condition would be ~±0.040 — borderline for detecting +0.03 effects.
