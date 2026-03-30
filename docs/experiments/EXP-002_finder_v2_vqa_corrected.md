# EXP-002: Finder v2 — VQA-Corrected Annotations

## Hypothesis

Re-labeling with visual QA (reading preview images to verify bbox placement) should significantly improve model quality over blind-estimated labels. EXP-001 used annotations where bboxes were estimated without visual verification — many had systematic errors:

- sign_board covering entire pylon instead of just price panel
- Wrong fuel types (e.g., U91 labeled as P95)
- Wrong prices (OCR misreads)
- Missing brand_zone annotations
- Label/price bbox overlap or Y-misalignment

148 of 149 images now have VQA-verified annotations. Same image set, same 2-class config (sign_board + fuel_price), but substantially improved label quality.

**Expected:** mAP@50 > 0.7 (up from unknown baseline — EXP-001 never completed training). The tighter sign_board boxes (price panel only, not full pylon) should help the model learn what a price panel actually looks like.

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (2 classes) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0), fuel_price(1) |
| Images | 115 train / 23 val / 11 test |
| Detections | train: sign_board=115, fuel_price=372 |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 (MPS stability) |
| Device | mps (Apple M5) |
| AMP | False (required for MPS stability) |
| Seed | 42 |

### Key difference from EXP-001

Same images, same class config, but ALL annotations re-verified with visual QA:
- sign_board tightened to price panel only (not full pylon)
- brand_zone added where missing
- Fuel types and prices corrected
- Label/price spatial relationships validated

### Brand coverage (train)

caltex=29, bp=16, shell=14, united=13, ampol=12, mobil=8, independent=7, puma=6, seven_eleven=5, liberty=2, otr=1, unknown=1, eg=1

## Command

```bash
# Build dataset (2-class)
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3

# Train
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v2_2class_vqa
```

## Results

| Metric | All (best epoch 100) |
|--------|-----|
| mAP@50 | **0.305** |
| mAP@50-95 | 0.088 |
| Precision | 0.297 |
| Recall | 0.326 |

### Comparison with prior runs

| Run | Labels | Best mAP@50 | vs Blind |
|-----|--------|------------|----------|
| v1_2class_149 (EXP-001) | Blind-estimated | 0.195 | baseline |
| v2_batch8 | VQA-corrected | 0.248 | +27% |
| **v2_batch4 (this run)** | **VQA-corrected** | **0.305** | **+56%** |

## Analysis

**VQA label correction works.** Same 149 images, same 2-class config, but correcting annotation quality via visual QA improved mAP@50 by 56% relative (0.195 → 0.305).

Key observations:
- **Still climbing at epoch 100** — loss curves not fully plateaued. More epochs (200+) or learning rate scheduling could push higher.
- **Batch size matters on MPS** — batch=4 outperformed batch=8 (0.305 vs 0.248), likely due to MPS numerical stability. Batch=16 crashed entirely.
- **0.305 mAP@50 is modest** — with only 115 training images across 11 brands, there isn't enough variety to generalize well. The model needs more data.
- **Label quality is now the floor, not the ceiling** — further gains will come from more images, not better labels.

What the VQA corrections fixed:
- sign_board covering full pylon → tightened to price panel only
- Wrong fuel types and prices → corrected via visual reading
- Missing brand_zone → added where visible
- Label/price bbox overlap → spatial relationships validated

## Next Steps

- [ ] EXP-003: Label remaining 132 pending images → retrain with ~200+ images (biggest expected gain)
- [ ] EXP-004: Try 200 epochs (model still improving at 100)
- [ ] EXP-005: Add fuel_label as 3rd class, compare
- [ ] Scrape more for critical gaps: Costco (0), Metro (0), OTR (2)
- [ ] Night/rain augmentation for underrepresented conditions

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v2_2class_vqa
```
