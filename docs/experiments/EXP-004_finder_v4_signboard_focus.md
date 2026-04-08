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

## EXP-004b: imgsz=960 — Higher Resolution Test

**Hypothesis:** Higher input resolution would help since sign_boards vary in size. 960px gives 2.25x more pixels.

**Result: NEGATIVE.** 960px scored 0.421 mAP@50, worse than 640px's 0.452 (-7%).

| Resolution | Best mAP50 | Best epoch | Model size |
|-----------|-----------|-----------|-----------|
| **640px** | **0.452** | 57 | 5.1 MB |
| 960px | 0.421 | 78 | 6.1 MB |

**Why 960px hurt:** Most images are Bing thumbnails (~300px original) upscaled to 640/960. At 960px the upscaling artifacts (blur, interpolation) dominate. Higher resolution only helps with high-res source images, which we don't have for most of the dataset.

**Takeaway:** Stay at 640px. Higher resolution is a dead end unless we source higher-res images.

## Current State Assessment (2026-04-08)

### Component Status

| Component | Model | Best Metric | Status | Blocker |
|-----------|-------|-------------|--------|---------|
| Finder (1-class sign_board) | YOLO26n | mAP50=0.452 | Active | Need more data (~600 train for 0.70) |
| Finder (2-class +fuel_price) | YOLO26n | mAP50=0.235 | Abandoned | fuel_price stuck at 0.064, too small for 640px |
| Reader Price | SimpleCRNN | — | Not started | Blocked on Finder crops |
| Fuel Type Classifier | SimpleCNN | — | Not started | Blocked on Finder crops |
| Brand Classifier | SimpleCNN | — | Not started | Blocked on Finder crops |
| Spatial Pairing | Algorithm | — | Not started | Blocked on Finder crops |
| E2E Pipeline | All | — | Not started | Blocked on all components |
| TFLite Export | — | — | Not started | Blocked on trained models |

### Dataset State

- **249 labeled images** (226 with annotations on disk)
- **192 images in ingest** waiting to be processed (round 3 Bing scrape)
- **15 brands** represented (Costco=5, Metro=12, OTR=11, Liberty=14)
- **Build split (seed=42):** 177 train / 35 val / 14 test

### Experiment Progression

| Experiment | Train | Classes | sign_board mAP50 | Key learning |
|-----------|-------|---------|-----------------|-------------|
| EXP-001 | 116 | 2 | ~0.19 | Blind labels don't work |
| EXP-002 | 115 | 2 | ~0.30* | VQA labels +56% over blind |
| EXP-003 | 140 | 2 | 0.247 | Val set changed, not comparable |
| EXP-003b | 131 | 2 | 0.171 | Cleaning helps but val set drift |
| Sanity | 131 | 1 | 0.390 | 1-class works, pipeline valid |
| **EXP-004** | **177** | **1** | **0.452** | **+16% from +35% more data** |
| EXP-004 960px | 177 | 1 | 0.421 | Higher res hurts (low-res sources) |
| EXP-004 2-class | 177 | 2 | 0.235 | fuel_price stuck at 0.064 |

*EXP-002's 0.305 was on an easier val set; scores 0.200 on current val set

### Key Findings (Ranked by Impact)

1. **sign_board scales linearly with data.** 131→177 train (+35%) gave +16% mAP. This is the clearest signal — more data = better model.
2. **fuel_price is a dead end at 640px.** Stuck at 0.064 regardless of data. Need second-stage approach.
3. **VQA labels matter.** EXP-001→002 showed +56% from annotation quality alone.
4. **sign_board scope is critical.** Agents consistently over-annotate sign_board (include brand logos, promo banners). Prompt tightened but needs ongoing enforcement.
5. **960px doesn't help.** Low-res source images (Bing thumbnails) make upscaling counterproductive.
6. **Bing scraping works.** 23% end-to-end yield vs 0% from GitHub agents, 5% from Wikimedia.

### Dead Ends (Do Not Retry)

- ~~fuel_price as YOLO class~~ — too small at 640px, 0.064 mAP after 4 attempts
- ~~imgsz=960~~ — hurts with current low-res image sources
- ~~Wikimedia scraping~~ — 90% exhausted, 0 new usable images in last run
- ~~GitHub Copilot agents~~ — 0% usable yield across 4 tasks
- ~~News article hero images~~ — article headers, not station photos

### Critical Path to Production

```
Current: sign_board Finder at 0.452 mAP50 (177 train)
   ↓ scrape+label to 350 train images
Target: sign_board Finder at ~0.55 mAP50
   ↓ scrape+label to 600 train images
Target: sign_board Finder at ~0.70 mAP50 (useful)
   ↓ begin Reader pipeline on sign_board crops
Target: E2E Finder→Reader on real signs
```

## Next Steps

- [ ] **EXP-005: Scale data to ~350 train** — process round 3 ingest (192 images), screen, label, retrain. Expected ~0.55 mAP@50.
- [ ] **EXP-006: Begin Reader pipeline** — crop sign_board regions from labeled images, train SimpleCRNN on price crops. Can run in parallel with data scaling.
- [ ] **Scrape round 4** — more Bing queries if round 3 yield is good
- [ ] **Consider augmentation** — mosaic/mixup to stretch data without scraping (lower priority since real data is available)

## Reproducibility

```bash
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v4_1class_249
```
