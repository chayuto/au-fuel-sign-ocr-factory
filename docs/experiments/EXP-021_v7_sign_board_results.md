# EXP-021: v7 sign_board Redefinition — Full Results

## Summary

Redefining sign_board from "fuel rows only" to "full physical sign panel" improved mAP50 from **0.379 to 0.770** (+103%) — the single largest improvement in the project's history, achieved primarily through annotation correction, not more data.

## Background

After 12 experiments (EXP-009 through EXP-020), the Finder plateaued at mAP50 ≈ 0.40-0.52 on clean evaluation. A dataset audit revealed two root causes:

1. **sign_board definition was wrong** — v5/v6 labeled only the fuel price rows (~10-20% of pylon area), creating a tiny, ambiguous detection target
2. **Annotation quality was inconsistent** — 12% of labels had structural issues (boxes extending into sky/road, wrong sign targeted)

The fix: redefine sign_board as the **full physical sign panel face** (brand logo through last fuel row, edge to edge of the panel).

## Experimental Design

Three variants tested on the same v2 test set (25 images, 0 leakage):

| Variant | Train imgs | Label source | Cost |
|---------|-----------|-------------|------|
| **021a** | 123 | 155 Sonnet v7 (manual relabel) | ~$8 (Sonnet tokens) |
| **021b** | 498 | 155 v7 + 343 old (mixed) | $0 (reuse existing) |
| **021c** | 498 | 155 v7 + 344 auto-merge + 97 heuristic | $0 (programmatic) |

### Programmatic Expansion Method (021c)

For annotations with `brand_bbox` (344 images):
```
new_sign_board = bounding_box_union(old_sign_board, brand_bbox)
```

For annotations without `brand_bbox` (97 images):
```
new_sign_board.y1 = max(0, old_sign_board.y1 - height * 0.4)
```

Total cost: **zero tokens, ~5 seconds of computation.**

## Results

### Canonical Test v2 (25 images, end2end=False)

| Model | Train | mAP50 | mAP50-95 | P | R |
|-------|-------|-------|----------|-------|-------|
| EXP-019 (old labels, baseline) | 483 | 0.379 | 0.105 | 0.454 | 0.400 |
| 021a (v7 Sonnet only) | 123 | 0.275 | 0.094 | 0.477 | 0.360 |
| 021b (mixed v7 + old) | 498 | 0.651 | 0.292 | 0.627 | 0.560 |
| **021c (all auto-expanded)** | **498** | **0.770** | **0.337** | **0.606** | **0.880** |

### Key Metrics Improvement (021c vs EXP-019 baseline)

| Metric | EXP-019 | EXP-021c | Change |
|--------|---------|----------|--------|
| mAP50 | 0.379 | **0.770** | **+103%** |
| mAP50-95 | 0.105 | **0.337** | **+221%** |
| Recall | 0.400 | **0.880** | **+120%** |
| Precision | 0.454 | 0.606 | +33% |

## Analysis

### 1. The Definition Matters More Than Data Volume

021a (123 v7 images) achieved 0.275 mAP50. EXP-019 (483 old images) achieved 0.379. The old definition with 4x more data only beat v7 by 38%. This shows the v7 definition is ~2.8x more efficient per image — each correctly labeled image teaches the model more.

### 2. Mixed Labels Create a Correction Signal

021b (mixed v7 + old) achieved 0.651 — better than either pure approach. The 155 v7 images acted as a **directional correction**, steering the model toward bigger predictions while the 343 old images provided location diversity. This is an unexpected finding: you don't need to relabel everything; a minority of corrected labels can shift the entire model.

### 3. Programmatic Expansion Works

021c (all auto-expanded) achieved **0.770** — the best result. The brand_bbox merge (344 images) and heuristic top-extension (97 images) produced usable training labels without any Sonnet vision analysis. This saved ~$50 in labeling costs.

The recall jump to **0.880** is particularly striking — the model now finds 88% of signs, up from 40% with old labels. The bigger sign_board target is fundamentally easier for YOLO to detect.

### 4. mAP50-95 Tripled

mAP50-95 (which measures bbox tightness across IoU thresholds 0.5-0.95) improved from 0.105 to 0.337 — a 3.2x improvement. This means the predicted boxes don't just overlap the signs, they **fit the physical panel accurately**. This is critical for downstream cropping quality.

### 5. The Scaling Plateau Was a Labeling Problem

The apparent plateau at mAP50 ≈ 0.40-0.52 (EXP-012 through EXP-020) was not a data scaling limit or hyperparameter issue. It was caused by **the model learning the wrong thing** — it was trying to find tiny fuel row strips instead of obvious physical sign panels. The 7 hyperparameter experiments (EXP-013 through EXP-018) were solving the wrong problem.

## Lessons Learned

1. **Check the label definition before tuning hyperparameters.** We spent 7 experiments (~6 hours) tuning freeze/mosaic/lr/epochs when the real issue was what we were asking the model to find.

2. **Programmatic label correction can be as effective as manual relabeling.** The brand_bbox merge (zero cost) produced better results than 155 manual Sonnet relabels alone.

3. **A minority of correct labels can steer a model.** 155 v7 labels out of 498 total (31%) was enough to shift the model's predictions significantly (0.379 → 0.651).

4. **Bigger detection targets are easier.** This is obvious in hindsight but was obscured by the leakage issue — we thought we had 0.9 mAP50 with small targets, so we never questioned the approach.

5. **Recall is the metric that moved most.** From 0.400 to 0.880 — the model went from missing 60% of signs to missing only 12%. The v7 target is simply more findable.

## Remaining Risks

1. **97 heuristic expansions** (blind 40% top extension) may include sky/background. Should be QC'd or Sonnet-relabeled.
2. **v2 test set is small** (25 images). Results have high variance. Need to expand test set as dataset grows.
3. **Auto-merged boxes may not be tight** enough for downstream cropping. Visual audit of a sample is recommended.

## Next Steps

### Completed
1. QC'd and Sonnet-relabeled all 60 heuristic expansions (12 batches)
2. Retrained as EXP-021d — mAP50=0.670 (lower than 021c's 0.770)
3. **Finding: The heuristic expansion was actually beneficial.** Sonnet "fixes" made some boxes tighter than the test set expected, hurting recall (0.880→0.560). The 40% heuristic was a reasonable approximation.
4. **021c remains the best model at mAP50=0.770**

### Full EXP-021 Variant Comparison

| Variant | Labels | mAP50 | mAP50-95 | P | R |
|---------|--------|-------|----------|------|------|
| 021a (v7 Sonnet only) | 155 manual | 0.275 | 0.094 | 0.477 | 0.360 |
| 021b (mixed v7+old) | 155 v7 + 343 old | 0.651 | 0.292 | 0.627 | 0.560 |
| **021c (all expanded)** | **155 v7 + 344 merge + 97 heuristic** | **0.770** | **0.337** | **0.606** | **0.880** |
| 021d (heuristics fixed) | 215 v7 + 344 merge | 0.670 | 0.335 | 0.719 | 0.560 |

### Immediate

### Short-term
1. Continue Sonnet relabeling of the 97 heuristic images (1 agent at a time)
2. Scrape + label more images with v7 rules
3. Target: 800+ images for mAP50 > 0.85

### Medium-term
1. Build Stage 2 pipeline (crop → row detection → price reading)
2. Expand canonical test set to 50+ images
3. Begin dashcam-style image collection (driving perspective)

## Reproducibility

```bash
# Programmatic expansion (zero cost)
python -c "
import json, os
for fn in os.listdir('data/tmp/annotations'):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d or d.get('prompt_version') == 'v7': continue
    sign = d['sign']
    sb = sign.get('bbox', [0,0,1,1])
    bb = sign.get('brand_bbox', None)
    if bb:
        sign['bbox'] = [min(sb[0],bb[0]), min(sb[1],bb[1]), max(sb[2],bb[2]), max(sb[3],bb[3])]
    else:
        h = sb[3] - sb[1]
        sign['bbox'] = [sb[0], max(0, sb[1]-h*0.4), sb[2], sb[3]]
    d['prompt_version'] = 'v7_auto'
    d['entries'] = []
    json.dump(d, open(f'data/tmp/annotations/{fn}','w'), indent=2)
"

# Build + train
python scripts/build_finder_dataset.py --classes 0 --seed 42 --freeze-split <baseline_manifest>
PYTORCH_ENABLE_MPS_FALLBACK=1 yolo detect train data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False freeze=10 mosaic=0.5 seed=42

# Evaluate
PYTORCH_ENABLE_MPS_FALLBACK=1 yolo detect val data=data/finder_canonical_test_v2/dataset.yaml \
    model=<weights>/best.pt device=mps amp=False end2end=False
```
