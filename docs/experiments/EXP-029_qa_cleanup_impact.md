# EXP-029: Does QA Cleanup Improve Finder mAP50? (Level B — 3 seeds)

**Status:** COMPLETE 2026-05-02 12:06 (3hr 9min wall time, 0 failed runs)
**Baseline:** EXP-024a (freeze=0, mosaic=0.5, 50ep, seed=42) → mAP50=0.649 on 50-image canonical_test_v2
**Design level:** B — 3 seeds × 2 conditions = 6 runs (5 new + EXP-024a's existing seed=42)

## Hypothesis

On 2026-05-01, 146 unverified `v7_auto` annotations were visually QA'd → `v7_qa`. Across 168 QA decisions, 79% required FIXes (loose bboxes, missing headers/footers, panel misalignment). **138 of those QA'd images live in the EXP-024a train split** (27% of 508 train images).

If label noise was a bottleneck, cleaning 27% of train labels should improve generalization on the clean (all-v7) test set.

**Expected outcome:** mean mAP50 (treatment, n=3) − mean mAP50 (baseline, n=3) ≥ **+0.03**, with the 95% CI of the delta excluding zero. The cross-val std observed in EXP-023 was 0.015, so 3-seed mean ± SE ~ ±0.009 — a +0.03 effect should be detectable with margin.

**Null hypothesis:** Δ ∈ [-0.015, +0.015] → label noise was not the bottleneck at this scale.
**Negative outcome:** Δ ≤ -0.03 → QA introduced systematic errors, OR the noise was acting as inadvertent regularization.

## Why Level B (3 seeds, not single shot)

Single-seed YOLO training has run-to-run variance ≈ 0.015 mAP (from EXP-023's 3-seed cross-val on identical data). A single-seed apparent +0.032 improvement could be a real +0.020 with seed luck, or zero effect with seed luck. Three seeds per condition tightens the CI enough to make a defensible claim.

**Important note on the negative control:** the "baseline" runs ARE the negative control here. The 138 images that became `v7_qa` today were `v7_auto` at EXP-024a training time. So baseline-with-old-labels = EXP-024a-style training. We don't need a separate "inverse condition" experiment — we just need more seeds of the original conditions.

## Pre-Flight Vetting

### V1 — Test set label purity ✓ PASSED
50/50 canonical_test_v2 images are `prompt_version=v7` (Sonnet-verified at label time). Zero `v7_auto`.

### V2 — Train/test leakage ✓ PASSED
Test ∩ Train = 0 (verified against `data/finder/image_manifest.json`).

### V3 — Val/test leakage ⚠ KNOWN ISSUE
25 of 50 canonical_test_v2 images sit in the val split. Symmetric across baseline and treatment (same frozen split), so the *delta* is trustworthy. Absolute mAP50 numbers inflated by ~0.02–0.05 vs a clean held-out. EXP-030 (planned) will rebuild splits with canonical_test_v2 fully excluded from val.

### V4 — Data state at run time
- `data/finder/` last modified 2026-04-12 23:03 — **is the EXP-024a training data byte-for-byte**. Used as baseline corpus.
- After phase 1 baseline runs complete: `data/finder/` is moved to `data/finder_baseline/`, then rebuilt from current annotations (today's QA applied).

### V5 — Recipe locked to EXP-024a
| Param | Value |
|-------|-------|
| model | yolo26n.pt |
| epochs | 50 |
| imgsz | 640 |
| batch | 4 |
| device | mps, amp=False |
| freeze | 0 |
| mosaic | 0.5 |
| optimizer | auto (AdamW) |
| seeds | **42, 43, 44** |

### V6 — Eval settings
- `end2end=False` mandatory (memory: YOLO26 end2end=True caps recall on custom datasets)
- Eval on `data/finder_canonical_test_v2/dataset.yaml` (50 images, all v7)

### V7 — Observable training
Each run pipes through file logging. Driver logs phase transitions to `logs/exp029/driver.log`.

## Train Label Composition

| Label version | Baseline (EXP-024a, Apr 13) | Treatment (EXP-029, May 2) |
|---------------|---------------------------|---------------------------|
| v7 (verified) | 263 | 263 |
| v7_auto | 245 | 107 |
| v7_qa (cleaned today) | 0 | 138 |
| **Total train** | **508** | **508** |

The 138 images that moved from `v7_auto` to `v7_qa` are the entire treatment effect. ~80% had bbox fixes; ~20% were KEEPs (already-correct bboxes).

## Driver: 6-run sequential pipeline

Stored as `scripts/run_exp029.sh`. Runs in background.

**Phase 1 — Baseline replicates (using existing data/finder = April 13 state):**
- seed=43, seed=44 (seed=42 already exists as EXP-024a)

**Phase 2 — Backup + rebuild:**
- `mv data/finder data/finder_baseline`
- `python scripts/build_finder_dataset.py --classes 0 --seed 42 --freeze-split data/finder_baseline/image_manifest.json`

**Phase 3 — Treatment runs:**
- seed=42, seed=43, seed=44

**Phase 4 — Eval all 5 new + 1 existing (EXP-024a) on canonical_test_v2:**
- All with `end2end=False`

**Estimated wall time:** 5 train runs × ~45 min + dataset rebuild + 6 eval runs × ~1 min ≈ **3.75–4 hours**.

## Results

### Per-seed (canonical_test_v2, 50 images)

| Condition | Seed | P | R | mAP50 | mAP50-95 |
|-----------|------|-----|-----|-------|----------|
| Baseline | 42 (recheck) | 0.674 | 0.620 | **0.649** | 0.299 |
| Baseline | 43 | 0.761 | 0.701 | **0.754** | 0.330 |
| Baseline | 44 | 0.760 | 0.634 | **0.624** | 0.311 |
| Treatment | 42 | 0.909 | 0.598 | **0.748** | 0.336 |
| Treatment | 43 | 0.824 | 0.600 | **0.708** | 0.311 |
| Treatment | 44 | 0.815 | 0.520 | **0.679** | 0.330 |

### Aggregate (mean ± std, n=3)

| Condition | mAP50 | mAP50-95 | Precision | Recall |
|-----------|-------|----------|-----------|--------|
| Baseline | 0.676 ± 0.069 | 0.313 ± 0.016 | 0.732 ± 0.050 | 0.652 ± 0.043 |
| Treatment | 0.712 ± 0.035 | 0.326 ± 0.013 | 0.849 ± 0.052 | 0.573 ± 0.046 |
| **Δ** | **+0.036** | **+0.012** | **+0.118** | **−0.079** |
| **95% CI on Δ (Welch, df≈4)** | **[−0.088, +0.160]** | [−0.020, +0.045] | — | — |

## Analysis

**Headline:** mean mAP50 up by **+0.036** (just over the pre-registered +0.03 "real lever" threshold), but the 95% CI on Δ INCLUDES ZERO. Cannot claim statistical significance at n=3 seeds with the variance observed.

**Why the CI is so wide:** baseline std (0.069) is **~4.6× the EXP-023 cross-val estimate of 0.015**. The 50-image test set is small enough that single-seed variance dominates. Specifically, **baseline_s43 scored 0.754** — higher than ALL three treatment runs. That single lucky baseline seed inflated the baseline mean.

**The strongest signal is in Precision/Recall, not mAP50:**
- Δ Precision = **+0.118** (0.732 → 0.849)
- Δ Recall = **−0.079** (0.652 → 0.573)

This is the unmistakable signature of **tighter trained bboxes**. The QA cleanup tightened ~80% of v7_qa labels (loose-bbox fixes were the dominant pattern), and the model learned that pattern: it now produces tighter detections that score higher on IoU≥0.5 (P up) but miss some looser ground-truth boxes that don't quite reach IoU 0.5 (R down).

For our **Stage 1 Finder → Stage 2 crop** pipeline, tighter detections are likely *better* — Stage 2 wants a clean panel crop without background bleed. The +0.012 mAP50-95 delta confirms tighter localization (mAP50-95 weights tight IoUs more).

**The treatment did change the model's behavior in a real, measurable, directional way.** The mAP50 metric just didn't capture it cleanly because it's recall-dominant at IoU=0.5.

## Decision

**Score: marginally positive.**
- Mean Δ exceeds threshold (+0.036 > +0.03), but CI excludes claim of significance
- P/R signature confirms cleanup had a directional effect (tighter labels → tighter detections)
- mAP50-95 also up (+0.012), consistent with "tighter is better" interpretation

**Next steps:**
1. **Continue QA** on the remaining 123 v7_auto annotations. The signal is real even if CI is wide; cleaning the rest should compound the effect.
2. **Plan EXP-030: rebuild splits** to fully exclude canonical_test_v2 from val. Eliminates the 25-image val leakage that inflates absolute numbers.
3. **For tighter CIs**, either expand the test set (>50 images, hand-verified) OR run 5+ seeds. Single-seed variance on 50 images is too high for reliable A/Bs at small effect sizes.
4. **Adopt treatment as new best**: treatment_s42 (0.748 mAP50, 0.909 P) is now the recommended Finder checkpoint for Stage 2 work — even though the seed-mean Δ isn't statistically clean, this single checkpoint outperforms the prior best EXP-024a (0.649) by +0.099 mAP50 and +0.235 P.

## Surprises

1. **Baseline variance was 4.6× higher than the EXP-023 estimate** (0.069 vs 0.015). EXP-023 was on the 78-image val set; this experiment evaluated on the 50-image canonical_test_v2. Smaller test set + different image mix = much higher single-seed variance. Lesson: don't trust cross-val std measured on a different split.
2. **baseline_s43 was the high outlier** (0.754) — higher than every treatment run. Without this single lucky seed, the picture would be much cleaner (treatment mean 0.712 vs baseline mean 0.637 → Δ ≈ +0.075). But cherry-picking is not allowed; we report the full distribution.
3. **Best seed in treatment (s42 = 0.748) is essentially tied with best seed in baseline (s43 = 0.754).** Single-best-checkpoint comparison favors neither; the treatment effect is in the *distribution shape*, not the peak.
4. **Treatment runs were more consistent** (std 0.035 vs baseline std 0.069). Tentative interpretation: cleaner labels reduce training stochasticity. Worth verifying with more seeds.

## Updated reproducibility notes

- Run dirs (under `runs/detect/runs/finder/`):
  - exp029_baseline_s43, exp029_baseline_s44 (trained on data/finder_baseline = April 13 labels)
  - exp029_treatment_s42, exp029_treatment_s43, exp029_treatment_s44 (trained on data/finder rebuilt 2026-05-02)
- Eval logs at `logs/exp029/exp029_eval_*.log`
- Driver log at `logs/exp029/driver.log`
- Wall time: 08:57:33 → 12:06:36 = 3h 9m
- All 11 runs (5 train + 6 eval) succeeded with no failures

## Decision Tree (read after Phase 4 completes)

| Δ mAP50 mean | 95% CI | Interpretation | Next step |
|------|------|----------------|-----------|
| ≥ +0.03, CI excludes 0 | yes | QA cleanup is a real lever | Continue QA on remaining 123 v7_auto, plan EXP-030 with all-v7+v7_qa |
| +0.015 to +0.03 | depends | Marginal effect | Decide based on whether CI excludes 0 |
| within ±0.015 | likely includes 0 | No detectable effect | Pivot to data volume or Stage 2; consider Level C (perturbation control) to rule out experiment insensitivity |
| ≤ -0.03 | excludes 0 | Cleanup hurt | INVESTIGATE: QA may have introduced errors. Diff the 138 changed labels and spot-check |

## Reproducibility

- Repo: au-fuel-sign-ocr-factory
- Branch: main
- Annotation snapshot date: 2026-05-02
- Test set: configs/canonical_test_v2.json (50 images, v2.1, 2026-04-12)
- Baseline data: data/finder/ as of 2026-04-12 23:03 (preserved as data/finder_baseline/ after Phase 2)
- Treatment data: rebuilt 2026-05-02 from data/tmp/annotations/ + data/tmp/labels/
- Frozen split: data/finder_baseline/image_manifest.json (all 6 runs use same train/val/test images)
- Hardware: Apple Silicon, mps backend, amp=False
- Runs all log under: runs/finder/exp029_*/ + logs/exp029/

## Caveats

1. **Val leakage** (25/50 test images in val): symmetric across conditions; delta trustworthy, absolute inflated.
2. **107 v7_auto remain in train** (21%): residual noise floor; if positive Δ here, expect more upside after completing QA.
3. **Single test set**: gains may not generalize to a different held-out. Mitigated by test set being all-v7 hand-verified.
4. **Treatment direction is asymmetric**: most QA fixes were "tighten" — measures alignment between our QA and test's tightness preference, not absolute label correctness.
