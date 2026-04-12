# EXP-016: Two-Class Model (sign_board + fuel_price)

## Motivation

All single-class experiments plateau around mAP50≈0.40 on clean data with ~458 training images. Each image provides only 1 sign_board box — minimal supervision signal. By adding fuel_price as a second class, each image provides 1 sign_board + ~3.2 fuel_price boxes = 4.2 boxes average. This is 3.2x more gradient signal per image without collecting a single new image.

The architecture already supports multi-class (YOLO26n), and our annotations already contain fuel_price bboxes in the JSON sidecars. We just need to include class 3 (fuel_price) in the build.

## Hypothesis

2-class training (sign_board + fuel_price) with the 012b recipe will push clean mAP50 for sign_board from 0.399 to **≥ 0.50** due to richer per-image supervision. The fuel_price boxes force the model to learn sign interior structure, which helps localize the sign_board as well.

**Note:** The canonical test v2 only has sign_board labels. fuel_price mAP will be measured on the experiment's own val split.

## Setup

| Parameter | Value | vs 012b |
|-----------|-------|---------|
| **classes** | **0,3 (sign_board + fuel_price)** | was 0 only |
| **nc** | **2** | was 1 |
| freeze | 10 | same |
| mosaic | 0.5 | same |
| epochs | 50 | same |
| imgsz | 640 | same |
| batch | 4 | same |
| Dataset | 561 total, frozen split, ~458 train | same |

Expected box count: ~458 sign_board + ~1,460 fuel_price = ~1,918 boxes (vs 458 in 1-class)

## Results

### Canonical Test v2 (25 images, CLEAN, end2end=False)

**Per-class results:**
| Class | Images | Instances | P | R | mAP50 | mAP50-95 |
|-------|--------|-----------|-------|-------|-------|----------|
| sign_board | 25 | 25 | 0.464 | 0.400 | **0.380** | 0.100 |
| fuel_price | 25 | 77 | 0.251 | 0.078 | 0.070 | 0.019 |
| **all** | 25 | 102 | 0.357 | 0.239 | 0.225 | 0.060 |

Best val epoch: 47 (mAP50=0.224). Training time: ~28 min.

### Comparison (sign_board mAP50 only, all clean v2)

| Model | Classes | Train boxes | sign_board mAP50 |
|-------|---------|-------------|-----------------|
| **012b** | **1 (sign_board)** | **451** | **0.399** |
| 016 | 2 (sign_board + fuel_price) | 1926 | 0.380 |
| 013 (defaults) | 1 | 458 | 0.294 |
| 015 (1024px) | 1 | 453 | 0.316 |
| 014 (no mosaic) | 1 | 453 | 0.229 |

## Analysis

**Hypothesis not confirmed.** 2-class training (0.380) slightly underperformed 1-class (0.399) for sign_board detection. The fuel_price class was very weak (0.070 mAP50).

### Why fuel_price Struggled

fuel_price boxes are small (each ~5-15% of sign area) and visually similar to each other (LED digits on dark background). With only Sonnet-estimated bboxes (not pixel-perfect), the annotation noise is proportionally larger for small boxes. The model can't learn precise localization from noisy small-box annotations.

### Why sign_board Didn't Improve

Adding the fuel_price task may have split the model's capacity. With freeze=10, only the detection head trains. The head now needs to distinguish 2 classes instead of 1, with less capacity per class. The multi-task gradient interference may have offset the benefit of more supervision.

### Key Takeaway

At current annotation quality, single-class (sign_board only) remains optimal. fuel_price detection requires tighter bbox annotations (possibly from the sign_board detector itself — detect sign → crop → annotate prices within crop).

## Next Steps

- 012b (1-class, freeze=10, mosaic=0.5) remains best clean model at mAP50=0.399
- Multi-class is not beneficial until annotation quality for small boxes improves
- Next: try unfreezing fewer layers (freeze=5) or varying weight_decay
