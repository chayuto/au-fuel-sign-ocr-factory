# Compute Sprint Plan — Training & Inference Experiments

## Current Baseline

| Metric | Value |
|--------|-------|
| Model | EXP-021d (YOLO26n) |
| mAP50 | 0.731 (50-image verified test) |
| mAP50-95 | 0.283 |
| P / R | 0.829 / 0.640 |
| Train images | 498 |
| Recipe | freeze=10, mosaic=0.5, 50ep, auto→AdamW |

---

## EXP-023: Cross-Validation (3 seeds) — ~1.5 hours

### Hypothesis
The observed mAP50=0.731 on the 50-image test set has a standard deviation of **< 0.03**, meaning our results are stable enough to detect real improvements of ≥0.05.

### Why
We've only ever trained with seed=42. Every comparison we've made assumes the seed doesn't matter — but random weight initialization, data shuffling, and augmentation order all change with the seed. If the variance is high (std > 0.05), then the difference between 0.72 and 0.76 is noise, and we've been chasing ghosts. If variance is low (std < 0.03), we can trust our measurements.

**This is the most important experiment in the sprint.** Everything else depends on knowing our measurement precision.

### Runs
| Run | Seed | Recipe |
|-----|------|--------|
| 23a | 42 | freeze=10, mosaic=0.5, 50ep |
| 23b | 123 | same |
| 23c | 7 | same |

### Success criteria
- std < 0.03 → proceed with confidence
- std 0.03-0.05 → results are directional but noisy
- std > 0.05 → need more test images or more stable training

---

## EXP-024: Freeze Ablation on v7 Labels — ~1 hour

### Hypothesis
With v7 sign_board labels (bigger, structural targets), **freeze=0 (all layers trainable)** will outperform freeze=10, achieving mAP50 ≥ 0.76.

### Why
The freeze=10 recommendation came from the YOLO26 training guide for data-scarce scenarios. The logic was: with <1K images, the COCO pretrained backbone knows more about visual features than your tiny dataset can teach, so lock it.

But v7 changed the game. The detection target is now a **large physical structure** (30-50% of frame), not a tiny strip of LED digits. The COCO backbone was trained to detect objects like cars, people, and animals — not fuel sign panels. With v7's bigger, clearer targets, the backbone might benefit from learning fuel-sign-specific features: the characteristic rectangular panel shape, LED glow patterns, brand color schemes.

We tested freeze=0 vs freeze=10 before (EXP-013 vs 012b), but that was on old labels with a noisy test set. The result was ambiguous. Time to re-test on clean data.

### Runs
| Run | freeze | Recipe |
|-----|--------|--------|
| 24a | 0 | mosaic=0.5, 50ep |
| 24b | 5 | mosaic=0.5, 50ep |
| baseline | 10 | (from 23a) |

### Success criteria
- freeze=0 beats freeze=10 by ≥0.03 mAP50 → unfreeze is worth the overfitting risk
- freeze=0 ties or loses → keep freeze=10, the backbone generalization is more valuable

---

## EXP-025: Longer Training (100 epochs) — ~30 min

### Hypothesis
With v7 labels (cleaner, less ambiguous), **100 epochs will improve over 50 epochs** by ≥0.02 mAP50, unlike with old labels where 100 epochs caused head overfitting.

### Why
On old labels (EXP-018), 100 epochs was worse than 50 — the model overfit to noisy labels after epoch ~50. But v7 labels are cleaner and more consistent. The model has more "real signal" to learn from, so additional epochs may extract more value instead of memorizing noise.

The YOLO26 training guide says <1K images → 50 epochs. But that advice assumed noisy labels and tiny targets. With v7's clean, large targets, the effective signal-to-noise ratio is higher, potentially supporting longer training.

### Runs
| Run | Epochs | Recipe |
|-----|--------|--------|
| 25a | 100 | freeze=10, mosaic=0.5 |
| baseline | 50 | (from 23a) |

### Success criteria
- 100ep > 50ep by ≥0.02 → training was under-baked, use 100ep going forward
- 100ep ≈ 50ep → 50ep is sufficient, save time
- 100ep < 50ep → overfitting still occurs, stick with 50ep

---

## EXP-026: Model Size (YOLO26s) — ~1 hour

### Hypothesis
YOLO26s (7M params) will outperform YOLO26n (2.5M params) by ≥0.03 mAP50, indicating the nano model is capacity-limited at 500+ images.

### Why
YOLO26n was chosen for the <15MB total model budget constraint. At 2.5M params, it's the smallest YOLO26 variant. With ~500 training images, we may have more data than the model can effectively use — the learning curves might be capacity-limited rather than data-limited.

If YOLO26s significantly outperforms, we have two options:
1. Use YOLO26s for training and distill to YOLO26n for deployment (knowledge distillation)
2. Accept the larger model (~10MB) if the budget allows

If YOLO26n matches YOLO26s, we know the bottleneck is data, not model capacity — and we should focus entirely on data collection.

### Runs
| Run | Model | Params | Recipe |
|-----|-------|--------|--------|
| 26a | yolo26s.pt | 7M | freeze=10, mosaic=0.5, 50ep |
| baseline | yolo26n.pt | 2.5M | (from 23a) |

### Success criteria
- YOLO26s > YOLO26n by ≥0.03 → capacity-limited, consider distillation
- YOLO26s ≈ YOLO26n → data-limited, focus on collection
- YOLO26s < YOLO26n → small model regularizes better, stay with nano

---

## EXP-027: Full Mosaic Augmentation — ~30 min

### Hypothesis
With v7's bigger targets, **mosaic=1.0 will match or beat mosaic=0.5**, achieving mAP50 ≥ 0.73.

### Why
We found mosaic=0.5 optimal on old labels because the tiny fuel-row targets got lost in mosaic's 4-image stitching. Mosaic creates extreme scale/position variation — good for generalization but destructive if the target is already hard to find.

v7 targets are 2-3x larger. They should survive mosaic distortion better. Full mosaic would give the model maximum scale diversity — important for the dashcam use case where signs appear at wildly varying distances.

If this works, we can remove mosaic=0.5 from the recipe (one less hyperparameter to tune).

### Runs
| Run | mosaic | Recipe |
|-----|--------|--------|
| 27a | 1.0 | freeze=10, 50ep |
| baseline | 0.5 | (from 23a) |

### Success criteria
- mosaic=1.0 ≥ mosaic=0.5 → use 1.0 (simpler, more augmentation)
- mosaic=1.0 < mosaic=0.5 by ≥0.03 → keep 0.5

---

## EXP-028: SAHI Sliced Inference (no retraining) — ~30 min

### Hypothesis
Running SAHI on the 50-image test set with 320×320 slices will improve mAP50 by **≥0.05** over standard inference, especially on distant/small signs.

### Why
SAHI is an inference-time technique — no retraining needed. It slices the image into overlapping patches, runs YOLO on each patch (where small signs appear larger relative to the patch), then merges predictions. Published results show +5-15% AP improvement on small objects.

In our dashcam scenario, signs at 50-100m distance are small in the frame. SAHI effectively gives us multi-scale detection without changing the model. If it works well, we could use SAHI during the "approach phase" (sign is distant) and standard inference when the sign is close.

**This is the only experiment that improves deployment performance with zero training cost.**

### Runs
| Run | Method | Slice size |
|-----|--------|-----------|
| 28a | SAHI | 320×320, overlap=0.2 |
| 28b | SAHI | 480×480, overlap=0.2 |
| baseline | Standard | 640×640 full image |

### Success criteria
- SAHI > standard by ≥0.05 → adopt for distant signs in dashcam pipeline
- SAHI ≈ standard → signs are already large enough in our test set

---

## EXP-029: Pseudo-Labeling (Semi-Supervised) — ~2 hours

### Hypothesis
Using our current model to auto-label the ~2000 unlabeled images (filtered by confidence > 0.8), then retraining on labeled + pseudo-labeled data, will improve mAP50 by **≥0.03**.

### Why
We have ~2000 images in `data/tmp/` that were scraped but skipped during labeling (no visible sign, too distant, wrong brand, etc.). But our model might find signs in some of them that the labeling agents missed — or the model might correctly identify images that DO have signs but were skipped due to human error.

Pseudo-labeling uses the model's own high-confidence predictions as "free" labels. The risk is confirmation bias (the model reinforces its own errors), but filtering by high confidence (>0.8) mitigates this. Published results show 10-20% more effective training data from pseudo-labeling.

**This is the only experiment that increases training data without any scraping or labeling cost.**

### Runs
1. Run inference on all ~2000 unlabeled images
2. Filter predictions with confidence > 0.8
3. Add pseudo-labels to training set
4. Retrain with recipe

### Success criteria
- mAP50 improves ≥0.03 → pseudo-labeling adds real value
- mAP50 unchanged → pseudo-labels are redundant
- mAP50 drops → confirmation bias, discard pseudo-labels

---

## EXP-030: Copy-Paste Augmentation — ~30 min

### Hypothesis
Adding `copy_paste=0.5` to the training recipe will improve mAP50 by **≥0.02** by increasing sign appearance diversity without new data.

### Why
Copy-paste augmentation crops detected objects from one training image and pastes them onto random backgrounds from other training images. This creates novel sign+background combinations the model hasn't seen, increasing effective dataset diversity.

YOLO26 supports this natively via `copy_paste=0.5`. It's especially useful when the dataset has limited background variety (which ours does — most images are suburban Australian streets).

### Runs
| Run | copy_paste | Recipe |
|-----|-----------|--------|
| 30a | 0.5 | freeze=10, mosaic=0.5, 50ep |
| baseline | 0.0 | (from 23a) |

### Success criteria
- copy_paste helps by ≥0.02 → add to recipe
- no change or hurts → leave at 0.0

---

## Execution Priority

| Priority | Experiment | Time | Why first |
|----------|-----------|------|-----------|
| 1 | EXP-023 (cross-validation) | 1.5h | **Must know variance before trusting any comparison** |
| 2 | EXP-028 (SAHI) | 30m | Free improvement, no training |
| 3 | EXP-024 (freeze ablation) | 1h | Biggest open architecture question |
| 4 | EXP-029 (pseudo-labeling) | 2h | Free data, biggest potential upside |
| 5 | EXP-025 (100 epochs) | 30m | Quick test |
| 6 | EXP-026 (YOLO26s) | 1h | Capacity question |
| 7 | EXP-027 (mosaic=1.0) | 30m | Recipe simplification |
| 8 | EXP-030 (copy-paste) | 30m | Easy augmentation test |

**Total: ~7.5 hours if running all. Pick top 4-5 for a 4-hour sprint.**
