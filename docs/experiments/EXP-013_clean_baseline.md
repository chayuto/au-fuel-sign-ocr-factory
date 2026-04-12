# EXP-013: Clean Baseline — First Leakage-Free Evaluation

## Motivation

EXP-012 discovered that the canonical test set v1 had severe data leakage (14/19 images in training). All prior mAP50 numbers were inflated. A new canonical test v2 (25 images, verified zero overlap with training) was created.

The only prior clean evaluation was EXP-012b (frozen split, freeze=10, mosaic=0.5) at mAP50=0.399 — but it used the "data-scarce recipe" which appeared to hurt on the few clean evaluations available.

This experiment establishes the **first true baseline**: default hyperparameters, maximum data, clean evaluation.

## Hypothesis

Default YOLO26n hyperparameters (no freeze, mosaic=1.0, 100 epochs) on ~458 training images will achieve **mAP50 ≥ 0.50** on canonical test v2, outperforming 012b's recipe (0.399).

**Basis:** EXP-008 (defaults) got 0.515 on v2 with 405 train images, vs 010-B (recipe) at 0.464. Defaults consistently outperform the freeze+mosaic recipe on clean data. With ~53 more training images, we expect further improvement.

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Dataset | 561 total: **458 train** / 78 val / 25 test |
| Split | `--freeze-split` from 506-image baseline manifest |
| freeze | **None** (default — all layers trainable) |
| mosaic | **1.0** (default) |
| epochs | **100** |
| optimizer | auto (→ AdamW lr=0.002) |
| batch=4, imgsz=640, device=mps, amp=False, seed=42 | |
| Evaluation | `canonical_test_v2` (25 images), `end2end=False` |
| Leakage check | **0/25 v2 test images in train** — VERIFIED CLEAN |

## Results

### Training Metrics
Best epoch: 84 (val mAP50=0.489, P=0.585, R=0.423)

### Canonical Test v2 (25 images, CLEAN, end2end=False)

| Model | Train | Recipe | v2 mAP50 | mAP50-95 | P | R |
|-------|-------|--------|----------|----------|-------|-------|
| EXP-012b | 451 | freeze=10, mosaic=0.5, 50ep | **0.399** | **0.123** | 0.410 | 0.440 |
| **EXP-013** | **458** | **defaults (100ep)** | **0.294** | **0.097** | **0.482** | **0.320** |

### Truly Clean Comparison (both verified 0/25 leakage)

| Model | Leaked v2 imgs | v2 mAP50 | Status |
|-------|---------------|----------|--------|
| EXP-008 | 13+/25 (est) | ~~0.515~~ | LEAKED |
| EXP-010-B | 13+/25 (est) | ~~0.464~~ | LEAKED |
| EXP-012 | 13/25 | ~~0.596~~ | LEAKED |
| **EXP-012b** | **0/25** | **0.399** | **CLEAN** |
| **EXP-013** | **0/25** | **0.294** | **CLEAN** |

## Analysis

### Hypothesis Rejected

Defaults (0.294) underperformed the freeze+mosaic recipe (0.399) by -26% on truly clean data. My earlier conclusion that "defaults win" was based on leaked evaluations.

### Revised Understanding

On truly clean data, the freeze+mosaic recipe IS better:
- **freeze=10** preserves COCO backbone features that generalize to unseen images
- **mosaic=0.5** reduces over-augmentation on small datasets
- **50 epochs** prevents head overfitting

Default training (all layers trainable, mosaic=1.0, 100 epochs) memorizes the training set but doesn't generalize — exactly the pattern we'd expect from overfitting.

### True State of the Finder

Best verified clean mAP50 is **0.399** (EXP-012b). The model detects ~40% of sign boards correctly on images it has never seen. This is early-stage — significant work needed to reach deployment quality (~0.80+).

## Next Steps

1. The freeze+mosaic recipe is validated as better — use it going forward
2. Try additional strategies from the YOLO26 training guide (docs/research/)
3. Need ~2-3x more diverse training data to approach 0.80 mAP50

## Reproducibility

```bash
# 1. Build with frozen split (preserves val/test, new → train)
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42 \
    --freeze-split /tmp/finder_baseline/image_manifest.json

# 2. Verify zero leakage
python -c "
import json, os
v2 = set(f.replace('.jpg','') for f in json.load(open('configs/canonical_test_v2.json'))['test'])
train = set(os.path.splitext(f)[0] for f in os.listdir('data/finder/images/train'))
assert len(v2 & train) == 0, f'LEAK: {v2 & train}'
print('CLEAN')
"

# 3. Train (defaults, 100 epochs)
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v12_1class_561_clean seed=42 \
    2>&1 | tee runs/finder/v12_clean_train.log

# 4. Evaluate on v2 (ALWAYS end2end=False)
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
    data=data/finder_canonical_test_v2/dataset.yaml \
    model=<save_dir>/weights/best.pt \
    device=mps amp=False end2end=False
```
