---
name: fuel-sign-labeler
description: |
  Stage 1 Labeler: Annotates sign_board bounding boxes on full camera photos for Finder training.
  Find the physical sign panel in the photo and draw ONE bbox per image.
  Use this skill when the user wants to label images for the Finder model.
---

# Stage 1: Fuel Sign Finder Labeler (Gemini Way)

## 2-Stage Labeling Pipeline Overview

- **Stage 1 (THIS SKILL):** Find the physical sign panel face (sign_board) → 1 bbox per image.
- **Stage 2 (LATER):** Read the cropped sign → fuel rows, prices, brand.

**This skill is Stage 1 ONLY.** Just find the sign.

### Data Quality Mandate

- Every bbox must be visually verified.
- If unsure where the sign panel edges are, SKIP the image. A missing label is better than a wrong label.
- **sign_board = the physical sign panel face** (v7 rules).

## What to Annotate: ONE Box

**sign_board = the physical sign panel face.**
The rectangular face containing the brand header and fuel price rows.

```
INCLUDE:
- Brand logo panel physically attached to the same pylon.
- Co-brand panels (Coles, Woolworths, etc.) physically part of the sign.
- Promo panels ("Save 4c") physically part of the sign face.
- All fuel type + price rows.
- Physical frame/edges of the sign panel.

EXCLUDE:
- Pylon pole/column structure below the sign.
- Separate signs not physically attached (Car Wash, ATM).
- Sky, ground, trees, buildings, cars.
```

## Workflow: For Each Image

### Step 1: Read and Classify
Read the image using `read_file` or `generalist`.
**SKIP if:** Not a photo, not Australian, no fuel price sign visible, or sign <10% of image.

### Step 2: Draw ONE Bounding Box
Estimate the sign_board bbox as `[x1, y1, x2, y2]` in normalized [0,1].

### Step 3: Write Files

**JSON sidecar** → `data/tmp/annotations/{stem}.json`:
```json
{
  "prompt_version": "v7",
  "image": { "file": "example.jpg", "source": "web", "conditions": { "time_of_day": "day", "weather": "clear" } },
  "sign": { "bbox": [0.25, 0.10, 0.75, 0.90], "brand": "shell", "sign_type": "led" },
  "entries": []
}
```

**YOLO label** → `data/tmp/labels/{stem}.txt`:
```
0 0.500000 0.500000 0.500000 0.800000
```
(Class 0, center-x, center-y, width, height)

### Step 4: Validate and Preview
```bash
.venv/bin/python scripts/validate_annotations.py data/tmp/annotations/{stem}.json
.venv/bin/python scripts/draw_annotations.py --files {stem}
```
**READ the preview.** Does the green box wrap the physical sign panel face?

### Step 5: Update Manifest
Update `data/tmp/labeling_manifest.csv` row for the image (status=done, has_sign=yes, etc.).
Log the event using `scripts/pipeline_logger.py`.
