# EXP-003: Finder v3 — Expanded Dataset (202 labeled images)

## Hypothesis

More data is the primary bottleneck. EXP-002 achieved mAP@50=0.305 with 115 train images and was still climbing at epoch 100. Adding ~35% more labeled images (140 train, up from 115) should push mAP@50 above 0.4. The new images add critical gap-brand coverage (OTR +2, Metro +2) and diverse sources (YouTube thumbnails, news articles, web).

Also extending to 200 epochs since EXP-002 loss curves weren't plateaued at 100.

**Expected:** mAP@50 > 0.4 (up from 0.305)

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (2 classes) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0), fuel_price(1) |
| Images | 140 train / 28 val / 11 test |
| Detections | train: sign_board=140, fuel_price=455 |
| Epochs | 200 |
| Image size | 640 |
| Batch size | 4 (MPS stability — batch=8 underperformed in EXP-002) |
| Device | mps (Apple Silicon) |
| AMP | False (required for MPS stability) |
| Seed | 42 |

### Key differences from EXP-002

- **+25 train images** (115 → 140), +5 val images (23 → 28)
- **+2 OTR** (was 1), **+2 Metro** (was 0), **+1 BP** (news source)
- **200 epochs** (was 100) — EXP-002 was still improving at epoch 100
- New sources: YouTube thumbnails, news articles, web/blog images

### Brand coverage (train)

caltex=34, bp=20, independent=16, shell=16, united=13, ampol=12, mobil=10, puma=6, seven_eleven=5, otr=2, liberty=2, metro=2, unknown=1, eg=1

## Command

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=200 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v3_2class_expanded
```

### Design rationale

- **Independent variable:** Dataset size (115 → 140 train images) and epoch count (100 → 200)
- **Dependent variable:** mAP@50 on val set
- **Control:** EXP-002 (same model, same classes, same hyperparams except data size and epochs)
- **Why not other experiments first:**
  - Adding fuel_label (3-class) — risks degrading sign_board/fuel_price before baseline is solid
  - Synthetic augmentation — real data gaps are the bottleneck, not data diversity
  - Architecture changes — YOLO26n is the right size; data quality matters more

### Pre-experiment state

| Component | Status | Best Metric | Notes |
|-----------|--------|-------------|-------|
| Finder (2-class) | EXP-002 baseline | mAP@50=0.305 | Still climbing at 100 epochs |
| Reader Price | Not started | — | Blocked on Finder |
| Fuel Type Classifier | Not started | — | Blocked on Finder |
| Brand Classifier | Not started | — | Blocked on Finder |
| Dataset | 202 labeled, 179 with annotations on disk | — | 140 train / 28 val / 11 test |

**Success criteria:** mAP@50 > 0.4 (31% relative improvement)
**Failure criteria:** mAP@50 < 0.32 (no improvement over EXP-002 despite +22% data)

## Results

Early stopping triggered at epoch 165 (no improvement for 100 epochs). Best model at **epoch 65**.

### Best model (best.pt, epoch 65) — final validation

| Metric | All | sign_board | fuel_price |
|--------|-----|-----------|-----------|
| mAP@50 | **0.247** | **0.387** | **0.107** |
| mAP@50-95 | 0.103 | 0.177 | 0.030 |
| Precision | 0.296 | 0.281 | 0.311 |
| Recall | 0.273 | 0.536 | 0.011 |

### Peak mAP@50 during training (from results.csv)

| Epoch | mAP@50 |
|-------|--------|
| 105 | 0.276 |
| 104 | 0.264 |
| 119 | 0.262 |
| 99 | 0.260 |
| 66 | 0.252 |

### Comparison with prior runs

| Run | Train images | Epochs | Best mAP@50 | vs EXP-002 |
|-----|-------------|--------|------------|------------|
| EXP-001 (blind labels) | 116 | 100 | 0.195 | — |
| EXP-002 (VQA labels) | 115 | 100 | 0.305 | baseline |
| **EXP-003 (expanded)** | **140** | **165 (early stop)** | **0.247** | **-19%** |

### Training dynamics

- Model reached peak ~0.276 around epoch 105, then oscillated 0.20-0.24 until early stopping at 165
- Train losses continued decreasing (box_loss 2.7→1.4, cls_loss 5.1→1.4) — clear overfitting
- **fuel_price recall collapsed to 0.011** — model essentially stopped detecting prices

## Analysis

**Hypothesis REJECTED.** More data + more epochs did NOT improve performance. mAP@50 dropped from 0.305 → 0.247 (-19%). This is a surprising negative result.

### Why did performance drop with MORE data?

1. **Val set changed.** EXP-002 had 23 val images, EXP-003 has 28. The 5 new val images likely include harder examples (YouTube thumbnails, news crops) that the model struggles with. The metrics may not be directly comparable due to different val sets.

2. **fuel_price detection collapsed.** Recall=0.011 means the model finds almost no prices. sign_board is OK (recall=0.536, mAP50=0.387). The new images may have introduced confusing price patterns (partial crops, angled signs, composite news images) that hurt price detection.

3. **Overfitting despite more data.** With batch=4 and 200 epochs, the model overfits the training set. Train loss drops to 1.4 while val loss stays at 2.7+. The small batch size may amplify noise.

4. **New image sources are harder.** YouTube thumbnails are 1280x720 with signs occupying <10% of frame. News composites have signs cropped at edges. These are fundamentally harder than the Wikimedia station photos that dominated EXP-001/002.

### EXP-003b: Cleaned dataset (removed 11 bad images)

Audited all 198 labeled images visually. Found and removed 11 problematic labels:
- 4 composites (news stitches, product catalog)
- 2 extreme close-up crops (no station context)
- 2 signs too small (<5% of frame)
- 1 pump transaction display (not a sign)
- 1 stylized photo (polaroid filter + text overlay)
- 1 duplicate close-up

**EXP-003b results** (131 train / 26 val, 200 epochs):

| Metric | All | sign_board | fuel_price |
|--------|-----|-----------|-----------|
| mAP@50 | 0.171 | 0.279 | 0.062 |

### Fair comparison: EXP-002 model on CURRENT val set

The key insight: EXP-002's reported 0.305 was on its own 23-image val set. When we evaluate the EXP-002 model on the current 26-image val set:

| Model | Own val set | Current val set (26 imgs) |
|-------|-----------|-------------------------|
| EXP-002 | **0.305** | **0.200** |
| EXP-003 | 0.247 | — |
| EXP-003b | — | **0.171** |

**The 0.305 was inflated by an easier val set.** On the same val set, EXP-002 gets 0.200 vs EXP-003b's 0.171 — a gap of only 0.029, not 0.134.

The true model performance is ~0.17-0.20 mAP@50, regardless of which training set. The val set composition matters more than the training improvements we've made so far.

### Root cause

The fundamental bottleneck is NOT data quantity or quality at this point. With ~130-140 clean training images across 11+ brands:
- sign_board detection is OK (0.28-0.32 mAP50)
- fuel_price detection is very weak (0.06-0.08 mAP50) — small objects, highly variable appearance

fuel_price bboxes are tiny relative to the image and vary enormously across brands/sign types. The nano model may need:
- More aggressive augmentation (mosaic, mixup)
- Higher resolution (960 instead of 640)
- More epochs with cosine LR schedule instead of early stopping

## Next Steps

- [ ] **EXP-004: Fixed val/test split** — pin val/test images by hash to enable fair comparison across experiments
- [ ] **EXP-005: Higher resolution (imgsz=960)** — fuel_price objects are tiny; larger input may help
- [ ] **EXP-006: Augmentation tuning** — increase mosaic/mixup probability for small object detection
- [ ] **Pipeline improvements done** — updated screening prompts to catch composites, pump displays, close-ups, and size threshold raised to ≥15%

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=200 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v3_2class_expanded
```
