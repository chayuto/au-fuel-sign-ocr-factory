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

_Training in progress..._

| Metric | sign_board | fuel_price | All |
|--------|-----------|-----------|-----|
| mAP@50 | | | |
| mAP@50-95 | | | |
| Precision | | | |
| Recall | | | |

## Analysis

_To be filled after training._

## Next Steps

_To be filled after training. Possible directions:_
- [ ] Compare with EXP-001 (if results exist) to quantify VQA label improvement
- [ ] EXP-003: Add fuel_label as 3rd class
- [ ] EXP-004: Label remaining 132 pending images → more data
- [ ] Night/rain augmentation for edge cases

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v2_2class_vqa
```
