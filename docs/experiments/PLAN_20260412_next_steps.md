# Research Plan — 2026-04-12

## Current State

**Best model:** EXP-021d — mAP50=0.760, mAP50-95=0.379 (verified honest evaluation)
**Dataset:** 596 annotations (309 Sonnet v7, 287 v7_auto merge)
**Test set:** 25 verified images (too small for reliable measurement)
**Architecture:** v7 sign_board = physical sign panel face, 1-class Finder

## What We Learned (2026-04-11 to 2026-04-12)

### Breakthroughs
1. **v7 sign_board redefinition** — physical panel instead of fuel rows. +89% mAP50 (0.403→0.760)
2. **Data leakage discovery** — invalidated all prior metrics (EXP-004–011). Built clean test set v2.
3. **Evaluation integrity** — caught 3 separate ground truth issues. Test labels must be hand-verified.

### Failed Approaches (valuable negative results)
- Hard negatives (EXP-009): counterproductive at <1K images
- SGD nano lr (EXP-011): AdamW better for small datasets
- imgsz=1024 (EXP-015): batch=2 too small
- 2-class model (EXP-016): fuel_price bboxes too noisy
- Programmatic label expansion (EXP-021c): inflated metrics from matching noisy labels

### Key Principles Established
- **Good data is good data.** No shortcuts on labels.
- **Test set labels are sacred.** Every one hand-verified.
- **Step-by-step validation.** Verify before proceeding at every stage.
- **Accept real numbers.** Don't game evaluation for better metrics.

## Next Steps (Priority Order)

### 1. Expand Test Set to 50+ Images [HIGH]

**Why:** 25 images is too noisy — can't distinguish 0.72 from 0.76 reliably. Need 50+ for ±5% confidence interval.

**How:**
- Move 25 diverse images from current val split to permanent test set
- Sonnet v7 label each one (test labels must be perfect)
- Update configs/canonical_test_v2.json
- Update --freeze-split baseline

**Estimated effort:** ~5 labeling batches, 1 hour

### 2. Scrape + Label 200+ New Images with v7 [HIGH]

**Why:** More data is the clearest path to mAP50 > 0.85. Each new v7 image is ~0.001-0.004 mAP improvement.

**How:**
- Use winning scrape strategies (APCO regional, EG Foodary, state+brand)
- Label with v7 rules from scratch — 1 agent at a time, no shortcuts
- Build + train + evaluate after each batch of ~50

**Estimated effort:** 5-10 scrape rounds, 40-80 labeling batches, multiple training runs

### 3. Finish Relabeling 287 v7_auto Merge Annotations [MEDIUM]

**Why:** Auto-merge labels are decent (~80% OK from spot check) but contain errors — wrong brands, boxes extending into ground/sky. Lower priority than new data.

**How:** Continue 1 agent at a time, 5 per batch. Currently at line 86 of /tmp/v7_auto_remaining.txt.

**Estimated effort:** ~57 more batches, 10-15 hours

### 4. Begin Stage 2 Research [MEDIUM, blocked by #1]

**Why:** Finder at 0.76 mAP50 may be sufficient to start crop→price reading experiments.

**How:**
- Run Finder on training images → save crops
- Experiment with classical CV row detection (horizontal projection)
- Build Price Reader training dataset from crops
- Activate sign-crop-labeler skill

**Estimated effort:** Research phase, 2-3 sessions

### 5. Retrain After All Labels Fixed [LOW, blocked by #3]

**Why:** Once all 596 are Sonnet v7 verified, retrain for cleanest possible model.

**How:** Standard recipe (freeze=10, mosaic=0.5, 50ep). Evaluate on expanded 50+ test set.

## Success Criteria

| Milestone | Metric | Target |
|-----------|--------|--------|
| Reliable evaluation | Test set size | 50+ images |
| Finder deployment quality | mAP50 on 50+ test | > 0.85 |
| Finder bbox quality | mAP50-95 | > 0.45 |
| Stage 2 viable | Price Reader accuracy on crops | > 80% character accuracy |
| Product demo | End-to-end pipeline | Detect → crop → read prices on 10 sample images |

## Research Philosophy

This project follows the scientific method with emphasis on data integrity:

1. **Hypothesize** with expected numbers
2. **Validate** dataset integrity before every experiment
3. **Experiment** with the smallest change that tests the hypothesis
4. **Measure** on verified ground truth only
5. **Document** everything — including failures
6. **Accept** real results — never optimize for metrics over product quality
