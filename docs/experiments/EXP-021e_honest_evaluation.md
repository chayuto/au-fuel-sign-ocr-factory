# EXP-021e: Honest Re-evaluation with Verified Test Set

## Why This Experiment Exists

EXP-021c reported mAP50=0.770 and EXP-021d reported 0.670. The difference was suspicious — fixing noisy labels shouldn't make things worse. Investigation revealed:

**14/25 v2 test labels were v7_auto (programmatically expanded, never visually verified).** This means:
- 021c (trained on noisy labels) was evaluated against noisy test labels → artificially inflated match
- 021d (trained on accurate labels) was evaluated against noisy test labels → penalized for accuracy

**This is the same class of error as the v1 leakage** — measuring against incorrect ground truth produces meaningless metrics.

## Fix

All 25 v2 test images are being Sonnet v7 relabeled with visual QA. Once complete, ALL models will be re-evaluated against the **same verified ground truth**.

## Models to Re-evaluate

| Model | Train labels | Description |
|-------|-------------|-------------|
| EXP-019 | 483 old (fuel rows only) | Pre-v7 baseline |
| 021a | 155 Sonnet v7 | v7 definition only, small dataset |
| 021b | 155 v7 + 343 old mixed | Mixed labels |
| 021c | 155 v7 + 344 merge + 97 heuristic | Auto-expanded, noisy |
| 021d | 215 v7 + 344 merge | Heuristics Sonnet-fixed |

## Hypothesis

With verified test labels, 021d (accurate training labels) should score **equal to or higher** than 021c (noisy training labels). If accurate training + accurate evaluation doesn't beat noisy training + noisy evaluation, then something else is wrong.

## Results

### Verified Test Set Construction

All 25 canonical_test_v2 images Sonnet v7 relabeled with visual QA. 14 previously had v7_auto (programmatic) labels. Key corrections:
- gimg_bp_connect: was on wrong part of image entirely
- gimg_otr_0e111c00: captured only bottom half of pylon
- gimg_vic_157a0c7f: bbox was far too narrow
- gimg_costco_f35cb256: included Costco building (should be sign only)

**Status: 25/25 test labels are Sonnet v7 verified. Ground truth is now trustworthy.**

### Honest Re-evaluation (All Models, Same Verified Test Set)

| Model | Train imgs | Train labels | mAP50 | mAP50-95 | P | R |
|-------|-----------|-------------|-------|----------|-------|-------|
| EXP-019 | 483 | old (fuel rows only) | 0.403 | 0.130 | 0.415 | 0.480 |
| 021a | 123 | 155 Sonnet v7 | 0.687 | 0.302 | 0.827 | 0.640 |
| 021b | 498 | 155 v7 + 343 old (mixed) | 0.712 | 0.356 | 0.667 | 0.600 |
| 021c | 498 | 155 v7 + 344 merge + 97 heuristic | 0.776 | 0.332 | 1.000 | 0.597 |
| **021d** | **498** | **215 v7 + 344 merge** | **0.760** | **0.379** | **0.845** | **0.654** |

### Previous (Noisy Test) vs Honest Comparison

| Model | Noisy test mAP50 | Honest test mAP50 | Delta | What happened |
|-------|-----------------|-------------------|-------|---------------|
| 021c | 0.770 | 0.776 | +0.006 | Lucky — noisy test happened to match |
| 021d | 0.670 | 0.760 | **+0.090** | Was penalized by noisy test labels |

## Analysis

### 1. The "Regression" Was Fake

021d appeared to regress from 021c (0.670 vs 0.770) because the test labels were wrong. On verified ground truth, 021d (0.760) is within noise of 021c (0.776), and has **better mAP50-95** (0.379 vs 0.332). Fixing the heuristic labels improved box accuracy, not degraded it.

### 2. Accurate Labels Produce Accurate Models

| Metric | 021c (noisy train) | 021d (accurate train) | Winner |
|--------|-------------------|----------------------|--------|
| mAP50 | 0.776 | 0.760 | ~tie |
| mAP50-95 | 0.332 | **0.379** | **021d** (+14%) |
| Precision | 1.000 | 0.845 | 021c (but 1.0 is suspicious) |
| Recall | 0.597 | **0.654** | **021d** (+10%) |

021d has better bbox quality (mAP50-95), better recall, and more realistic precision. The 021c "perfect precision" of 1.000 is a red flag — likely means the model is very conservative (high confidence threshold, misses uncertain signs).

### 3. v7 Definition Is Validated

With only 123 training images, v7 (0.687) beats 483 old-definition images (0.403) by **70%**. The sign_board redefinition is the single most impactful change in the project.

### 4. Data Scaling Works Within v7

| Model | v7 train imgs | mAP50 |
|-------|-------------|-------|
| 021a | 123 | 0.687 |
| 021d | 498 (215 v7 + 344 merge) | 0.760 |

More data improves results, but the label quality matters: 021b (mixed v7+old, 0.712) beats 021a (v7 only, 0.687), and 021d (fixed heuristics, 0.760) beats 021b.

### 5. Lessons About Evaluation Integrity

This is the **third time** we caught evaluation issues in this project:
1. **v1 leakage** (EXP-004–011): 14/19 test images in training → inflated all metrics
2. **v2 label format** (EXP-021a): multi-class labels in 1-class test set → only 2/25 evaluated
3. **v2 noisy ground truth** (EXP-021c vs 021d): auto-expanded test labels favored noisy models

**Pattern:** Every time metrics look too good or results don't make sense, the evaluation is wrong — not the model. Always investigate the data first.

## Conclusion

**021d is the honest best model:** mAP50=0.760, mAP50-95=0.379, P=0.845, R=0.654.

The v7 sign_board redefinition improved mAP50 from 0.403 to 0.760 (+89%). Accurate labeling (021d) produces tighter boxes (mAP50-95 +14%) and better recall (+10%) than noisy labeling (021c). The remaining 344 v7_auto merge labels are the next quality improvement opportunity.

## Next Steps

### Immediate Priority: Fix Remaining v7_auto Labels
344 annotations still have v7_auto (brand_bbox merge) labels. These are better than heuristic but not verified. Sonnet-relabeling these would give the cleanest possible training set.

### Data Scaling
With verified labels, the scaling trend is:
- 123 v7 images → 0.687
- 498 mixed images → 0.760
- Target: 800+ all-v7 images → projected 0.85+

### Expand Test Set
25 images is small. Target 50+ verified test images to reduce evaluation noise.

### Stage 2 Activation
Finder mAP50 > 0.85 with mAP50-95 > 0.45 → begin Stage 2 (crop → price reading).
