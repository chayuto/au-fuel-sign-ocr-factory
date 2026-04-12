---
license: apache-2.0
library_name: ultralytics
tags:
  - yolo
  - object-detection
  - fuel-station
  - australia
  - ocr-pipeline
  - edge-ai
  - sign-detection
datasets:
  - custom
metrics:
  - mAP
pipeline_tag: object-detection
---

# AU Fuel Sign Finder — YOLO26n

A lightweight object detector that locates fuel price sign boards (pylons) in Australian petrol station photos. Designed as the first stage of an edge OCR pipeline: **Find sign → Crop → Read prices**.

## Model Description

| | |
|---|---|
| **Architecture** | YOLO26n (Ultralytics) |
| **Task** | Object Detection (1 class: `sign_board`) |
| **Parameters** | ~2.5M |
| **Input** | 640x640 RGB |
| **Target** | Australian fuel station pylon/canopy price signs |
| **Training data** | 509 manually labeled images (405 train / 78 val / 26 test) |
| **Brands covered** | Shell, BP, Ampol, Caltex, 7-Eleven, United, Costco, Liberty, Puma, Metro, Mobil, OTR, APCO, EG, independent |

## Performance

Evaluated on a frozen 19-image canonical test set across all training rounds:

| Experiment | Train images | mAP@50 | mAP@50-95 | Precision | Recall |
|-----------|-------------|--------|-----------|-----------|--------|
| EXP-004 | 177 | 0.348 | 0.146 | — | — |
| EXP-005 | 239 | 0.595 | 0.208 | — | — |
| EXP-007 | 296 | 0.725 | 0.274 | 0.863 | 0.684 |
| **This model** | **405** | **0.809** | **0.443** | **0.669** | **0.769** |

## Showcase

Detection results on unseen test images:

### Ampol — Night (LED pylon)
![Ampol night detection](showcase_ampol_night.jpg)

### Shell / Coles Express — Day (pylon with promo panels)
![Shell Coles day detection](showcase_shell_coles_day.jpg)

### 7-Eleven / Mobil — Dusk
![7-Eleven dusk detection](showcase_7eleven_dusk.jpg)

## Usage

```python
from ultralytics import YOLO

model = YOLO("best.pt")
results = model("fuel_station_photo.jpg", conf=0.3)

for box in results[0].boxes:
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    conf = box.conf[0].item()
    print(f"sign_board: ({x1:.0f},{y1:.0f}) to ({x2:.0f},{y2:.0f}) conf={conf:.2f}")
```

## Intended Use

- First stage of a mobile fuel price OCR pipeline
- Locating fuel price sign boards in street-level photography
- Research on Australian fuel station signage detection

**Not intended for:** Real-time video processing (not optimized for speed), non-Australian fuel stations, detecting individual price digits (that's the downstream Reader model's job).

## Training

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 yolo detect train \
    data=dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False seed=42
```

Best checkpoint at epoch 63. Training on Apple M-series (MPS backend).

## Dataset

509 images from diverse Australian sources: Wikimedia Commons, Flickr (CC-licensed), news articles, Google Images. Covers all major Australian fuel brands, LED/backlit/mechanical sign types, day/night/dusk conditions, urban/suburban/rural locations across VIC, NSW, QLD, SA, WA, TAS, ACT.

All annotations are bounding boxes in YOLO format (1 class: `sign_board`). The sign_board bbox covers only the fuel price rows — excluding brand logos, promotional panels, and pylon structure.

## Limitations

- Recall drops on distant/small signs (<15% of frame)
- Some false positives on non-fuel signage (shopping centre pylons, directory boards)
- Trained on Australian sign styles only — will not generalize to US/UK/European fuel stations
- Night/rain performance is weaker than daytime clear conditions
