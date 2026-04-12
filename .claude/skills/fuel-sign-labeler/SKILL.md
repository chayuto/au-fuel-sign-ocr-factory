---
name: fuel-sign-labeler
description: |
  Stage 1 Labeler: Annotates sign_board bounding boxes on full camera photos for Finder training.
  This is the FIRST stage of a 2-stage labeling pipeline.
  Stage 1 (this skill): Find the sign in the photo → 1 bbox per image
  Stage 2 (sign-crop-labeler): Read the cropped sign → fuel rows, prices, brand
  Use this skill when the user wants to label images for the Finder model.
---

# Stage 1: Fuel Sign Finder Labeler

## 2-Stage Labeling Pipeline Overview

```
Stage 1 (THIS SKILL):
  Input:  Full camera photo of a fuel station
  Output: 1 bounding box → sign_board (the physical sign panel)
  Purpose: Train the YOLO26n Finder model
  Speed:  ~30s per image, 1 box only

Stage 2 (sign-crop-labeler skill — LATER):
  Input:  Cropped sign image from Finder output
  Output: Fuel rows (type + price), brand classification
  Purpose: Train Price Reader, Fuel Type Classifier, Brand Classifier
  Speed:  ~2min per crop
  When:   After Finder reaches mAP50 > 0.70
```

**This skill is Stage 1 ONLY.** Do NOT annotate fuel rows, prices, or brand zones. Just find the sign.

### Data Quality Philosophy

**Accurate labeling is the foundation. No shortcuts, no heuristics, no "good enough."**

- Every bbox must be visually verified by reading the preview image. No exceptions.
- If the preview looks wrong, fix it. Don't mark as done and move on.
- If you're unsure where the sign panel edges are, skip the image. A missing label is better than a wrong label.
- Test set images require EXTRA care — they are the ground truth all models are measured against.
- Never use programmatic expansion or blind heuristics on labels. Every bbox must come from actually looking at the image.

## Prompt Version

**Current version: v7** (2026-04-12)

| Version | Date | Key Changes |
|---------|------|-------------|
| v1-v4 | 2026-03 | Initial versions, blind estimation, added QA |
| v5-v6 | 2026-04 | "Fuel rows only" sign_board, 4 classes annotated per image |
| **v7** | **2026-04-12** | **sign_board = full physical sign panel. 1 class only. brand_zone/fuel_label/fuel_price retired from Stage 1.** |

## What to Annotate: ONE Box

**sign_board = the physical sign panel face.**

The rectangular face of the pylon/sign structure that contains the brand header and fuel price rows. One box. That's it.

```
INCLUDE in sign_board:
┌─────────────────────┐ ←─┐
│    ★ CALTEX          │   │
│   ⓦ Woolworths       │   │  sign_board bbox
│ Save 4c per litre   │   │  (the whole panel face)
│ Unleaded    145.9   │   │
│ Diesel      127.9   │   │
│ LPG          52.5   │   │
└─────────────────────┘ ←─┘

EXCLUDE from sign_board:
    ║ pylon pole ║         ← structural support below
    separate car wash sign ← different sign
    sky / background       ← only the physical panel
    ground / road          ← not part of the sign
```

### Include:
- Brand logo panel at top (Caltex star, BP shield, Shell pecten, etc.)
- Brand elements **physically attached to the same pylon** (circular logo on top, co-brand panel)
- Co-brand panel (Woolworths, Coles Express, Foodary, etc.)
- Promo panels physically part of the sign face ("Save 4c", "Discount Fuel", "Wild Bean Cafe")
- All fuel type + price rows
- Physical frame/edges of the sign panel

### Exclude:
- Pylon pole/column structure (the metal/concrete support below the sign)
- Brand logos on a **separate pole** (e.g., Shell pecten mounted on a different pole from the price panel)
- Separate signs not physically attached (Car Wash, ATM, "UNIGAS" below the main sign)
- Sky, trees, buildings, cars
- Ground/pavement

### Edge Case: "Is this part of the same sign?"
**Rule: If it's physically attached to the same pylon structure, include it.** If it's on a separate pole or mounted independently, exclude it. The downstream Brand Classifier benefits from seeing the logo in the crop.

### Why the Full Panel?
- **Bigger detection target** → easier for YOLO to find
- **Includes brand logo** → downstream Brand Classifier needs it
- **Unambiguous** → "the sign face" is a clear physical object
- **Consistent** → every agent draws the same box

## Workflow: For Each Image

### Step 1: Read and Classify (fast reject)

Read the image. **Snap decision in 2 seconds:**

**SKIP immediately if:**
- Not a photo (clipart, chart, infographic, manufacturer render)
- Not Australian (US $/gallon, UK pence, Chinese factory)
- No fuel price sign visible (just pumps, canopy, building)
- Sign too small/distant (<10% of image area)
- Sports, politics, unrelated content

**HAS_SIGN if:**
- A fuel price sign panel is visible
- At least one price readable (XXX.X format)
- Sign occupies ≥10% of image area
- Real camera photo of an Australian station

### Step 2: Draw ONE Bounding Box

Estimate the sign_board bbox as `[x1, y1, x2, y2]` in normalized [0,1] coordinates.

**Tips:**
- Find the top edge of the brand header panel
- Find the bottom edge of the last fuel row
- Find the left and right edges of the physical sign face
- The box should tightly wrap the sign panel — not loose, not cutting into content

### Step 3: Write Files

**JSON sidecar** → `data/tmp/annotations/{stem}.json`:

```json
{
  "prompt_version": "v7",
  "image": {
    "file": "example.jpg",
    "source": "web",
    "conditions": {
      "time_of_day": "day",
      "weather": "clear"
    }
  },
  "sign": {
    "bbox": [0.25, 0.10, 0.75, 0.90],
    "brand": "caltex",
    "sign_type": "led"
  },
  "entries": []
}
```

**Note:** `entries` is empty in v7 Stage 1. Fuel row annotation happens in Stage 2 on the crop.

**YOLO label** → `data/tmp/labels/{stem}.txt`:

```
0 0.500000 0.500000 0.500000 0.800000
```

One line. Class 0 (sign_board), center-x, center-y, width, height.

### Step 4: Validate

```bash
.venv/bin/python scripts/validate_annotations.py data/tmp/annotations/{stem}.json
```

### Step 5: Preview and Verify

```bash
.venv/bin/python scripts/draw_annotations.py --files {stem}
```

**READ the preview.** Does the green box wrap the physical sign panel? Not too wide, not too narrow, not extending into sky/ground?

### Step 6: Update Manifest + Log

```bash
# Update manifest
.venv/bin/python -c "
manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
for i, line in enumerate(lines):
    if line.startswith('{filename},'):
        lines[i] = '{filename},{status},{has_sign},{brand},{sign_type},0,{quality},{agent_id},{timestamp}\n'
        break
with open(manifest, 'w') as f: f.writelines(lines)
"

# Log
.venv/bin/python scripts/pipeline_logger.py log \
    --image {filename} --stage label --agent {agent_id} \
    --action labeled --brand {brand}
```

## Metadata to Record

Even though we don't annotate fuel rows in Stage 1, record this metadata in the JSON:

- **brand**: shell, bp, ampol, caltex, seven_eleven, united, costco, liberty, puma, metro, mobil, otr, apco, eg, independent
- **sign_type**: led, backlit, mechanical, digital
- **time_of_day**: day, night, dusk
- **weather**: clear, overcast, rain

This metadata helps with dataset analysis and stratified splitting.

## Quality Checklist

Before marking done:
1. Is this a real Australian fuel station photo?
2. Does the green box wrap the PHYSICAL SIGN PANEL (brand header through last fuel row)?
3. Is the box NOT extending into sky, ground, cars, or pylon pole?
4. Did you READ the preview image?

**Skip aggressively. 1 clean annotation > 5 sloppy ones.**
