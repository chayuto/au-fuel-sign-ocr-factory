# EXP-001: Finder v1 — 2-Class Baseline (sign_board + fuel_price)

## Hypothesis

YOLO26n fine-tuned on 149 real Australian fuel sign images with **2 classes** (sign_board, fuel_price) will establish a strong baseline. Starting with 2 classes avoids the noisy fuel_label bboxes (12% overlap with prices, high size variance) and the sparse brand_zone annotations (only 61% coverage).

Expected mAP@50 > 0.6 on val set. fuel_price detection should be strong (bright LED digits are visually distinctive). sign_board should be straightforward (one per image, large bbox).

Key unknowns:
- How well do vision-estimated bboxes (not pixel-perfect) work for training?
- Is 116 train images enough for the nano model to generalize across 11 brands?
- Can fuel_price detections alone (without fuel_label) support downstream fuel type inference via row position?

## Design Decision: Why 2 Classes

Annotations store all 4 classes (sign_board, brand_zone, fuel_label, fuel_price) — the dataset builder selects per experiment via `--classes`.

| Class | This Exp | Rationale |
|-------|----------|-----------|
| sign_board (0→0) | Yes | Core — locates the price panel |
| brand_zone (1) | No | Opportunistic, only 61% annotated. Brand classifier can work on sign_board crop. |
| fuel_label (2) | No | Bbox quality issues: 12% overlap with prices, width std=60% of mean. Only 8 fuel types — classification not OCR. |
| fuel_price (3→1) | Yes | Core — LED digits are visually crisp, consistent format |

Future experiments can add fuel_label (3-class) or all 4 and compare.

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (2 classes) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0), fuel_price(1) |
| Images | 116 train / 22 val / 11 test |
| Detections | 496 train / 95 val / 49 test |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 16 |
| Device | mps (Apple Silicon) |
| AMP | False (required for MPS stability) |
| Optimizer | default (SGD) |
| Augmentation | default ultralytics |

### Class distribution (train)

| Class | Count |
|-------|-------|
| sign_board (0) | 116 |
| fuel_price (1) | 380 |

### Brand coverage (train)

caltex=29, bp=17, shell=15, ampol=14, united=12, seven_eleven=7, mobil=7, independent=6, puma=6, liberty=2, otr=1

## Command

```bash
# Build dataset (2-class)
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3

# Train
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=16 device=mps amp=False \
    project=runs/finder name=v1_2class_149
```

## Results

_To be filled after training._

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
- [ ] EXP-002: Add fuel_label as 3rd class, compare mAP
- [ ] EXP-003: All 4 classes, compare
- [ ] Label remaining 162 pending images → more data
- [ ] Add synthetic augmentation for night/rain edge cases
- [ ] Test on real phone camera captures
- [ ] Evaluate fuel type inference from price row position (no fuel_label needed?)

## Reproducibility

```bash
# Dataset build (2-class: sign_board + fuel_price)
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3 --seed 42

# Training
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=16 device=mps amp=False \
    project=runs/finder name=v1_2class_149
```
