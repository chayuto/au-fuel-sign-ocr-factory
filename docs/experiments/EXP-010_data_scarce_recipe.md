# EXP-010: YOLO26 Data-Scarce Training Recipe

## Motivation

EXP-008 established the current best Finder at mAP50=0.884 (end2end=False) using 509 images with **default hyperparameters**. EXP-009 showed that adding generic negatives is counterproductive at this scale. Rather than collecting more data, this experiment tests whether **hyperparameter tuning for data-scarce regimes** can extract more from the existing 509 images.

The YOLO26 training guide (docs/research/YOLO26_training_guide.md) identifies several default settings that are suboptimal for datasets under 1000 images:

| Parameter | Our Default (EXP-008) | Guide Recommendation | Rationale |
|-----------|----------------------|---------------------|-----------|
| `freeze` | None (all layers trainable) | **10** (lock backbone) | 509 images insufficient to learn better features than COCO pretrained backbone. Fine-tuning all layers risks catastrophic forgetting of generalized features. |
| `mosaic` | 1.0 (always on) | **0.5** (50% probability) | Full mosaic creates extreme distortion. With only 509 images, the model can't find consistent patterns through continuous heavy augmentation. |
| `lr0` | 0.01 (default) | **0.0054** (nano recipe) | Official YOLO26n COCO training recipe uses lower initial LR. |
| `lrf` | 0.01 (gentle decay) | **0.0495** (aggressive decay) | Nano models need large early conceptual leaps, then rapid annealing to fine-tune. |
| `epochs` | 100 | **50** | Guide: <1K images → 50 epochs to prevent overfitting. |
| `optimizer` | auto → AdamW(lr=0.002) | **MuSGD** (explicit) | Guide warns AdamW can cause NaN/instability with YOLO26's NMS-free dual head. Auto selected AdamW in EXP-008 despite guide recommending MuSGD. |

Additionally, EXP-008 used `optimizer=auto` which selected **AdamW(lr=0.002)**, ignoring the lr0/momentum settings entirely. This means our lr schedule was never actually the one we specified — AdamW auto-tuned its own rate.

## Hypothesis

Applying the YOLO26 data-scarce training recipe (`freeze=10, mosaic=0.5, lr0=0.0054, lrf=0.0495, epochs=50`) to the same 509-image dataset will:

1. **Maintain or improve mAP50** from 0.884 baseline (EXP-008, end2end=False)
2. **Improve mAP50-95** (tighter bbox localization) from 0.444 baseline — frozen backbone preserves COCO spatial features
3. **Reduce training time** by ~50% (50 vs 100 epochs)

**Expected:** mAP50 ≈ 0.88–0.92, mAP50-95 ≈ 0.45–0.50

**Risk:** Freezing the backbone too aggressively may prevent the model from adapting to fuel-sign-specific features (LED digits, pylon shapes) that differ significantly from COCO objects.

## Experimental Design

### Two Training Runs (A/B)

To isolate the impact of backbone freezing from the lr/augmentation changes:

| Run | Description | freeze | mosaic | lr0 | lrf | epochs | optimizer |
|-----|-------------|--------|--------|-----|-----|--------|-----------|
| **10-A** | Freeze only | 10 | 1.0 | 0.01 | 0.01 | 100 | auto |
| **10-B** | Full recipe | 10 | 0.5 | 0.0054 | 0.0495 | 50 | auto |

**Baseline (EXP-008):** freeze=None, mosaic=1.0, lr0=0.01, lrf=0.01, epochs=100, optimizer=auto

### Controlled Variables

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Dataset | 509 images (405 train / 78 val / 26 test), NO negatives |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |
| Evaluation | `end2end=False` on canonical 19-image test set |

### Success Criteria

| Metric | EXP-008 Baseline | Minimum Acceptable | Target |
|--------|-------------------|-------------------|--------|
| mAP50 (e2e=False) | 0.884 | ≥ 0.88 | ≥ 0.90 |
| mAP50-95 | 0.444 | ≥ 0.44 | ≥ 0.48 |
| Precision | 0.840 | ≥ 0.83 | ≥ 0.85 |
| Recall | 0.827 | ≥ 0.82 | ≥ 0.85 |

## Setup

### Run 10-A: Freeze Only

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Dataset | 509 images (405 train / 78 val / 26 test), no negatives |
| **freeze** | **10** |
| mosaic | 1.0 (default) |
| optimizer | auto → **AdamW(lr=0.002)** |
| epochs | 100 |
| imgsz=640, batch=4, device=mps, amp=False, seed=42 | |
| Run | `thai-id-nano-ocr-factory/runs/detect/runs/finder/v9a_1class_509_freeze` |

### Run 10-B: Full Data-Scarce Recipe

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Dataset | 509 images (405 train / 78 val / 26 test), no negatives |
| **freeze** | **10** |
| **mosaic** | **0.5** |
| **lr0** | **0.0054** (specified, but ignored by auto optimizer — see note) |
| **lrf** | **0.0495** (specified, but ignored by auto optimizer) |
| optimizer | auto → **AdamW(lr=0.002)** |
| **epochs** | **50** |
| imgsz=640, batch=4, device=mps, amp=False, seed=42 | |
| Run | `thai-id-nano-ocr-factory/runs/detect/runs/finder/v9b_1class_509_recipe` |

### Critical Observation: `optimizer=auto` Overrides lr0/lrf

Both runs used `optimizer=auto`, which selected **AdamW(lr=0.002, momentum=0.9)** and explicitly logged: `'optimizer=auto' found, ignoring 'lr0=0.0054' and 'momentum=0.937' and determining best 'optimizer', 'lr0' and 'momentum' automatically...`

This means the nano-specific lr schedule (lr0=0.0054, lrf=0.0495) from the training guide was **never actually applied**. The only differences between 10-A and 10-B that took effect were:
- `mosaic=0.5` (vs 1.0)
- `epochs=50` (vs 100)

To test the guide's lr schedule, a future experiment must use `optimizer=SGD` or `optimizer=MuSGD` explicitly, bypassing auto selection.

## Results

### Training Metrics (val split, 78 images, end2end=True default)

| Run | Best Epoch | Val P | Val R | Val mAP50 | Val mAP50-95 |
|-----|-----------|-------|-------|-----------|-------------|
| 10-A (freeze) | 42 | 0.467 | 0.410 | 0.430 | 0.118 |
| 10-B (recipe) | 42 | 0.643 | 0.333 | 0.413 | 0.091 |

Training time: 10-A ~50 min (100 epochs), 10-B ~25 min (50 epochs).

### Canonical Test Set (19 images, end2end=False)

| Model | P | R | mAP50 | mAP50-95 |
|-------|-------|-------|-------|----------|
| EXP-008 (baseline) | 0.840 | 0.827 | 0.884 | 0.444 |
| 10-A (freeze only) | 0.858 | 0.789 | 0.853 | 0.391 |
| **10-B (full recipe)** | **1.000** | **0.833** | **0.911** | **0.460** |

### Cross-Experiment Comparison (canonical 19, end2end=False)

| Model | Train imgs | Key Change | mAP50 | mAP50-95 | P | R | Delta mAP50 |
|-------|-----------|-----------|-------|----------|-------|-------|-------------|
| EXP-004 | 177 | — | 0.348* | 0.146* | — | — | — |
| EXP-005 | 239 | — | 0.595* | 0.208* | — | — | +71% |
| EXP-007 | 296 | — | 0.725* | 0.274* | 0.863 | 0.684 | +21.8% |
| EXP-008 | 405 | — | 0.884 | 0.444 | 0.840 | 0.827 | +21.9% |
| EXP-009 | 405+44neg | 44 negatives | 0.740 | 0.348 | 0.787 | 0.582 | −16.3% |
| 10-A | 405 | freeze=10 | 0.853 | 0.391 | 0.858 | 0.789 | −3.5% |
| **10-B** | **405** | **freeze=10, mosaic=0.5, 50ep** | **0.911** | **0.460** | **1.000** | **0.833** | **+3.1%** |

*Historical values (may use end2end=True)*

## Analysis

### Hypothesis Confirmed (10-B)

The data-scarce recipe improved over baseline:
- mAP50: 0.884 → **0.911** (+3.1%) — **exceeds target of 0.90**
- mAP50-95: 0.444 → **0.460** (+3.6%) — best ever, approaching target of 0.48
- Precision: 0.840 → **1.000** (+19%) — **zero false positives on canonical test**
- Recall: 0.827 → 0.833 (+0.7%) — stable
- Training time: ~55 min → **~25 min** (−55%)

### Ablation: What Mattered Most

Comparing 10-A and 10-B isolates the effect of `mosaic=0.5` + shorter training:

| Factor | 10-A (freeze only) | 10-B (freeze + mosaic=0.5 + 50ep) | Delta |
|--------|--------------------|------------------------------------|-------|
| mAP50 | 0.853 | 0.911 | +0.058 |
| P | 0.858 | 1.000 | +0.142 |

- **freeze=10 alone hurt slightly** (0.884 → 0.853, −3.5%). Freezing the backbone restricted adaptation and 100 epochs may have overfit the head.
- **mosaic=0.5 + fewer epochs was the decisive factor.** Reducing mosaic gave the model clearer training signal. 50 epochs prevented head overfitting.
- The lr schedule (lr0/lrf) was NOT tested because `optimizer=auto` overrode it.

### Why Reduced Mosaic Helps

With only 405 training images, full mosaic (stitching 4 images per frame) creates extreme visual distortion in every batch. The model must extract features from chaotic, scale-distorted composites. At this dataset size, the signal-to-noise ratio is too low for aggressive augmentation. Reducing to `mosaic=0.5` means half the batches show natural, undistorted images — giving the detection head cleaner gradient signals to learn from.

### Why Fewer Epochs Help

10-A (100 epochs, freeze=10) peaked at epoch 42 and then degraded — classic head overfitting. With the backbone frozen, only the neck and head parameters update, which have far fewer parameters and memorize the dataset faster. 50 epochs with `mosaic=0.5` is a better match for the effective model capacity.

### Untested Variables

The lr schedule (lr0=0.0054, lrf=0.0495) and optimizer choice (MuSGD vs AdamW) were NOT tested because `optimizer=auto` overrode all manual settings. These remain promising avenues:

```
optimizer=auto → AdamW(lr=0.002)  # What we actually ran
optimizer=SGD  → would respect lr0=0.0054, lrf=0.0495  # Untested
optimizer=MuSGD → recommended by YOLO26 guide  # Untested
```

## Next Steps

1. **10-B is the new production Finder model** — mAP50=0.911, P=1.0, R=0.833
2. **EXP-011 candidate: explicit MuSGD/SGD optimizer with nano lr schedule** — bypass `optimizer=auto` to actually test the training guide's lr0=0.0054/lrf=0.0495. This is the one variable we haven't been able to test.
3. **Upload 10-B to HuggingFace** — update the model card with corrected metrics
4. **More positive data** — scaling trend still productive; 100 more images could push toward 0.93+ mAP50
5. **Dataset versioning** — `build_finder_dataset.py` now saves `image_manifest.json` per build for reproducibility

## Reproducibility

```bash
# 0. Build dataset (NO negatives)
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

# 1. Rebuild canonical test set
.venv/bin/python -c "
import json, os, shutil, yaml
canon = json.load(open('configs/canonical_val_split.json'))
if os.path.exists('data/finder_canonical_test'): shutil.rmtree('data/finder_canonical_test')
os.makedirs('data/finder_canonical_test/images/test', exist_ok=True)
os.makedirs('data/finder_canonical_test/labels/test', exist_ok=True)
for name in canon['test']:
    stem = os.path.splitext(name)[0]
    for split in ['train','val','test']:
        for ext in ['.jpg','.jpeg','.png']:
            img, lbl = f'data/finder/images/{split}/{stem}{ext}', f'data/finder/labels/{split}/{stem}.txt'
            if os.path.exists(img) and os.path.exists(lbl):
                shutil.copy2(img, f'data/finder_canonical_test/images/test/{stem}{ext}')
                shutil.copy2(lbl, f'data/finder_canonical_test/labels/test/{stem}.txt')
                break
        else: continue
        break
yaml.dump({'path':os.path.abspath('data/finder_canonical_test'),'train':'images/test','val':'images/test','test':'images/test','nc':1,'names':{0:'sign_board'}}, open('data/finder_canonical_test/dataset.yaml','w'))
"

# 2a. Run 10-A: Freeze only
LOG_A=runs/finder/v9a_freeze_train.log && mkdir -p runs/finder
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    freeze=10 \
    project=runs/finder name=v9a_1class_509_freeze seed=42 \
    2>&1 | tee "$LOG_A"

# 2b. Run 10-B: Full data-scarce recipe
LOG_B=runs/finder/v9b_recipe_train.log
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False \
    freeze=10 mosaic=0.5 lr0=0.0054 lrf=0.0495 \
    project=runs/finder name=v9b_1class_509_recipe seed=42 \
    2>&1 | tee "$LOG_B"

# 3. Evaluate both — ALWAYS end2end=False
for MODEL in runs/finder/v9a_1class_509_freeze/weights/best.pt \
             runs/finder/v9b_1class_509_recipe/weights/best.pt; do
    echo "=== $MODEL ==="
    PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
        data=data/finder_canonical_test/dataset.yaml \
        model="$MODEL" device=mps amp=False end2end=False
done
```
