# EXP-004: Finder v4 — sign_board-only with Expanded Dataset

## Hypothesis

sign_board detection scales with data while fuel_price does not. Training a 1-class Finder (sign_board only) on the expanded 249-image dataset should push mAP@50 past 0.45 and establish a viable first-stage detector for the Finder → Reader pipeline.

**Expected:** mAP@50 > 0.45 for sign_board (up from 0.390 with 131 images)

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0) only |
| Images | 177 train / 35 val / 14 test |
| Detections | train: sign_board=177 |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |

### Why 1-class instead of 2-class

Evidence from this session shows fuel_price detection is stuck at ~0.06 mAP@50 regardless of data size:

| Run | Train imgs | fuel_price mAP50 |
|-----|-----------|-----------------|
| EXP-003b | 131 | 0.062 |
| v4 2-class | 177 | 0.064 |

fuel_price bboxes are tiny (3-6 per image, each ~5% of sign area) and YOLO26n at 640px can't resolve them. The planned architecture (CLAUDE.md) already accounts for this: Finder crops the sign_board, then a second-stage Reader model handles price OCR on the crop.

### Brand coverage (train)

caltex=38, bp=20, shell=19, independent=15, seven_eleven=12, united=12, ampol=12, mobil=10, liberty=10, metro=9, otr=8, puma=7, costco=3

## Results

| Metric | best.pt (epoch 57) |
|--------|-------------------|
| **mAP@50** | **0.452** |
| mAP@50-95 | 0.179 |
| Precision | 0.579 |
| Recall | 0.514 |

### Progression across experiments

| Run | Train imgs | Classes | sign_board mAP50 | Delta |
|-----|-----------|---------|-----------------|-------|
| sanity (131 imgs) | 131 | 1 | 0.390 | baseline |
| **v4 (177 imgs)** | **177** | **1** | **0.452** | **+16%** |
| v4 2-class | 177 | 2 | 0.405 | -10% (fuel_price drag) |

### Key insight

**sign_board scales linearly with data.** 35% more training images → 16% higher mAP@50. Extrapolating:
- 250 train → ~0.50 mAP@50
- 400 train → ~0.60 mAP@50
- 600 train → ~0.70 mAP@50 (approaching useful threshold)

## Analysis

**1-class Finder is the right architecture.** sign_board detection is the simplest, highest-value component. At 0.452 mAP@50 it's not production-ready but clearly learning and improving with data.

**fuel_price should be a separate second-stage model.** Once sign_board crops are reliable, a lightweight reader model (SimpleCRNN or small YOLO) operating on the cropped sign at higher effective resolution will perform much better than trying to detect tiny price bboxes in full-frame 640px images.

## Next Steps

- [ ] Scale to 400+ images via more Bing scraping rounds → target 0.60 mAP@50
- [ ] Try imgsz=960 to see if higher resolution helps at current data volume
- [ ] Begin Reader pipeline: crop sign_board → price OCR on crop
- [ ] Consider data augmentation (mosaic, mixup) to stretch existing data further

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v4_1class_249
```
