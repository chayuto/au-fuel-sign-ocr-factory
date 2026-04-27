# Data Pipeline — From Scraped Images to Production Dataset

**Last updated:** 2026-03-29

## Overview

This document defines how raw scraped images flow through the pipeline to become a production-grade YOLO training dataset. Every stage has explicit input/output formats, quality gates, and tooling.

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
│  Wikimedia  |  News  |  Street View  |  Manual  |  Synth    │
└──────┬──────┬────────┬──────────────┬──────────┬───────────┘
       │      │        │              │          │
       ▼      ▼        ▼              ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 0: RAW INGEST              data/raw/{batch}/         │
│  - Download, deduplicate, catalog                           │
│  - Output: raw images + source_manifest.json                │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: TRIAGE & QUALITY GATE   data/triaged/{batch}/     │
│  - Visual inspection (agent or human)                       │
│  - Grade: A/B/C/D + reject                                  │
│  - Output: triaged images + triage_report.json              │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: ANNOTATION              data/annotated/{batch}/   │
│  - Pre-annotate with Finder model (if trained)              │
│  - Manual correction via annotation UI                      │
│  - Output: images + annotation JSON (our schema)            │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: CONVERSION              data/finder_v{N}/         │
│  - Convert annotation JSON → YOLO labels                    │
│  - Train/val split (stratified by brand + entry count)      │
│  - Output: YOLO dataset (images/ + labels/ + dataset.yaml)  │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: READER CROPS            data/reader_experts/      │
│  - Extract label crops + price crops from annotated images  │
│  - Ground truth text from annotation                        │
│  - Output: crops/ + labels.txt (PP-OCR format)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Stage 0: Raw Ingest

### Directory Structure
```
data/raw/
├── wikimedia_2026-03-29/
│   ├── source_manifest.json
│   ├── au_fuel_sign_shell_leonora.jpg
│   ├── au_fuel_sign_mobil_albury.jpg
│   └── ...
├── news_scrape_2026-04-01/
│   ├── source_manifest.json
│   └── ...
└── manual_sydney_2026-04-05/
    ├── source_manifest.json
    └── ...
```

### Source Manifest (`source_manifest.json`)
```json
{
  "batch_id": "wikimedia_2026-03-29",
  "source_type": "web",
  "collected_date": "2026-03-29",
  "images": [
    {
      "file": "au_fuel_sign_shell_leonora.jpg",
      "source_url": "https://commons.wikimedia.org/...",
      "license": "CC BY-SA 4.0",
      "author": "Wikimedia user",
      "location": {"state": "WA", "suburb": "Leonora"},
      "md5": "abc123..."
    }
  ]
}
```

### Deduplication
- MD5 hash on raw file
- Cross-batch: check against all existing `source_manifest.json` files
- Perceptual hash (pHash) for near-duplicates (same sign, slightly different crop)

---

## Stage 1: Triage & Quality Gate

Every raw image gets a triage grade before annotation investment:

| Grade | Criteria | Action |
|-------|----------|--------|
| **A** | Sign fully visible, all prices legible, clear lighting | Annotate immediately |
| **B** | Sign visible, most prices readable, minor issues (angle, distance) | Annotate with effort |
| **C** | Sign partially visible or some prices illegible | Annotate what's visible, mark uncertain fields |
| **D** | Sign barely visible, too distant, heavy occlusion | Finder training only (sign_board bbox), skip Reader |
| **Reject** | No fuel sign visible, completely unusable | Remove from pipeline |

### Triage Report (`triage_report.json`)
```json
{
  "batch_id": "wikimedia_2026-03-29",
  "triage_date": "2026-03-29",
  "results": [
    {
      "file": "au_fuel_sign_shell_leonora.jpg",
      "grade": "A",
      "visible_brands": ["Shell"],
      "visible_fuel_count": 2,
      "notes": "Close-up, backlit sign, Unleaded + Diesel clearly readable"
    }
  ],
  "summary": {"A": 4, "B": 2, "C": 1, "D": 1, "reject": 1}
}
```

---

## Stage 2: Annotation

### Annotation Schema (JSON — our internal format)

This is the **master format**. All annotations live as JSON before conversion to YOLO.

```json
{
  "file": "au_fuel_sign_shell_leonora.jpg",
  "image_width": 3688,
  "image_height": 5673,
  "source": "web",
  "conditions": {
    "time_of_day": "day",
    "weather": "clear"
  },
  "sign": {
    "bbox": [0.12, 0.08, 0.88, 0.45],
    "brand": "shell",
    "sign_type": "backlit"
  },
  "brand_bbox": [0.15, 0.08, 0.85, 0.18],
  "entries": [
    {
      "row_index": 0,
      "fuel_type": "U91",
      "display_text": "UNLEADED",
      "price": 179.9,
      "price_text": "179.9",
      "label_bbox": [0.15, 0.20, 0.50, 0.30],
      "price_bbox": [0.55, 0.20, 0.85, 0.30],
      "confidence": "certain"
    },
    {
      "row_index": 1,
      "fuel_type": "DIESEL",
      "display_text": "DIESEL",
      "price": 176.9,
      "price_text": "176.9",
      "label_bbox": [0.15, 0.32, 0.50, 0.42],
      "price_bbox": [0.55, 0.32, 0.85, 0.42],
      "confidence": "certain"
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | yes | Image filename |
| `image_width`, `image_height` | int | yes | Original image dimensions (for bbox denormalization) |
| `source` | enum | yes | `manual`, `web`, `streetview`, `synthetic` |
| `sign.bbox` | [x1,y1,x2,y2] | yes | Normalized sign boundary |
| `sign.brand` | string | yes | Brand key from `configs/brands.yaml` |
| `sign.sign_type` | enum | yes | `led`, `mechanical`, `backlit`, `digital` |
| `brand_bbox` | [x1,y1,x2,y2] | no | Brand/logo area (null if brand not visible) |
| `entries[].row_index` | int | yes | 0-indexed row position (top to bottom) |
| `entries[].fuel_type` | enum | yes | Canonical fuel type from `configs/fuel_types.yaml` |
| `entries[].display_text` | string | yes | Exact text as shown on sign (e.g., "UNLEADED 91") |
| `entries[].price` | float | yes | Price in cents/litre (e.g., 179.9) |
| `entries[].price_text` | string | yes | Exact digits as shown (e.g., "179.9") — may differ from `price` if partially occluded |
| `entries[].label_bbox` | [x1,y1,x2,y2] | yes | Fuel type text region |
| `entries[].price_bbox` | [x1,y1,x2,y2] | yes | Price digit region |
| `entries[].confidence` | enum | yes | `certain`, `probable`, `uncertain` |

### Why `price` AND `price_text`?

- `price` is the ground truth numeric value (for validation, API cross-reference)
- `price_text` is the exact string rendered on the sign (for Reader training)
- They may differ: partially occluded sign → `price_text`: "1_9.9", `price`: 189.9 (from API lookup)

### Why `row_index`?

- Preserves vertical ordering of fuel entries on the sign
- Enables spatial consistency validation (row 0 should be above row 1)
- Some signs have a fixed order (E10, U91, P95, P98, Diesel) — can detect labeling errors

---

## Stage 3: YOLO Conversion

### Conversion Rules

Annotation JSON → YOLO labels (one `.txt` per image):

```
# Class mapping (from configs/finder_classes.yaml):
# 0 = sign_board, 1 = brand_zone, 2 = fuel_label, 3 = fuel_price

# Per image, one line per detection:
0 <cx> <cy> <w> <h>          ← sign.bbox (always 1 per image)
1 <cx> <cy> <w> <h>          ← brand_bbox (0 or 1 per image)
2 <cx> <cy> <w> <h>          ← entries[0].label_bbox
3 <cx> <cy> <w> <h>          ← entries[0].price_bbox
2 <cx> <cy> <w> <h>          ← entries[1].label_bbox
3 <cx> <cy> <w> <h>          ← entries[1].price_bbox
...                           ← repeat for each entry
```

### Example: 4-entry sign

```
0 0.500000 0.265000 0.760000 0.370000
1 0.500000 0.130000 0.700000 0.100000
2 0.325000 0.250000 0.350000 0.100000
3 0.700000 0.250000 0.300000 0.100000
2 0.325000 0.370000 0.350000 0.100000
3 0.700000 0.370000 0.300000 0.100000
2 0.325000 0.490000 0.350000 0.100000
3 0.700000 0.490000 0.300000 0.100000
2 0.325000 0.610000 0.350000 0.100000
3 0.700000 0.610000 0.300000 0.100000
```

**Line count per image:** 1 (sign) + 0-1 (brand) + 2×N (label+price per entry) = typically 7-13 lines.

### Dataset Structure

```
data/finder_v1/
├── train/
│   ├── images/
│   │   ├── wiki_shell_leonora.jpg
│   │   ├── wiki_mobil_albury.jpg
│   │   └── ...
│   └── labels/
│       ├── wiki_shell_leonora.txt
│       ├── wiki_mobil_albury.txt
│       └── ...
├── val/
│   ├── images/
│   └── labels/
└── dataset.yaml
```

### `dataset.yaml`
```yaml
path: data/finder_v1  # relative to repo root
train: train/images
val: val/images

nc: 4
names:
  0: sign_board
  1: brand_zone
  2: fuel_label
  3: fuel_price
```

### Train/Val Split Strategy

- **80/20 split** by default
- **Stratified by brand** — ensure each brand appears in both splits
- **Stratified by entry count** — ensure 3-entry, 4-entry, 5-entry signs distributed evenly
- **No same-sign leakage** — if multiple photos of same physical sign exist, all go to same split

---

## Stage 4: Reader Crops

### Extraction from Annotated Images

For each annotated entry, extract two crops:

```
data/reader_experts/
├── price/
│   ├── train/
│   │   ├── images/
│   │   │   ├── wiki_shell_leonora_price_0.png    ← crop of entries[0].price_bbox
│   │   │   ├── wiki_shell_leonora_price_1.png    ← crop of entries[1].price_bbox
│   │   │   └── ...
│   │   └── labels.txt                             ← PP-OCR format
│   └── val/
│       ├── images/
│       └── labels.txt
├── label/
│   ├── train/
│   │   ├── images/
│   │   │   ├── wiki_shell_leonora_label_0.png    ← crop of entries[0].label_bbox
│   │   │   └── ...
│   │   └── labels.txt
│   └── val/
└── vocab.txt                                      ← per expert
```

### Labels Format (PP-OCR style)

```
# labels.txt — tab-separated: image_path \t ground_truth_text
images/wiki_shell_leonora_price_0.png	179.9
images/wiki_shell_leonora_price_1.png	176.9
images/wiki_mobil_albury_price_0.png	176.9
images/wiki_mobil_albury_price_1.png	178.9
```

### Crop Preprocessing

- Denormalize bbox using image dimensions
- Add 5% padding around bbox (configurable)
- Resize to **height=48px**, maintain aspect ratio, pad to max_width=320px
- Save as PNG (lossless, preserves digit edges)

---

## Ground Truth Cross-Reference

### API-Assisted Labeling

For images with known station location + date:

1. Look up station in FuelWatch WA / FuelCheck NSW API
2. Get reported prices for that date
3. Cross-reference with OCR / manual reading
4. Resolve conflicts (API price vs visible price)

```json
{
  "file": "manual_bp_sydney_001.jpg",
  "captured_date": "2026-04-05",
  "station_id": "nsw_fuelcheck_12345",
  "api_prices": {
    "U91": 185.9,
    "P95": 205.9,
    "P98": 219.9,
    "DIESEL": 195.9
  },
  "annotation_prices": {
    "U91": 185.9,
    "P95": 205.9,
    "P98": 219.9,
    "DIESEL": 195.9
  },
  "match": true
}
```

---

## Production Dataset Spec

### Minimum Viable Dataset (MVP)

| Component | Target | Purpose |
|-----------|--------|---------|
| **Finder training** | 500 images (300 real + 200 synth) | Train YOLO26n to detect sign/brand/label/price |
| **Price Reader** | 2,000 real crops + 50K synth | Read price digits |
| **Label Reader** | 1,000 real crops + 50K synth | Read fuel type text |
| **Brand Classifier** | 50 images per brand × 13 brands = 650 | Classify station brand |

### Brand Distribution Target

| Brand | Min Images | Priority |
|-------|-----------|----------|
| Shell | 50 | HIGH (common) |
| BP | 50 | HIGH |
| Ampol | 50 | HIGH |
| 7-Eleven | 50 | HIGH |
| United | 30 | MEDIUM |
| Caltex | 30 | MEDIUM |
| Costco | 20 | MEDIUM |
| Liberty | 20 | LOW |
| Puma | 20 | LOW |
| Metro | 15 | LOW |
| Mobil | 15 | LOW |
| OTR | 15 | LOW |
| Independent | 15 | LOW |

### Sign Type Distribution Target

| Type | Min Images | Notes |
|------|-----------|-------|
| LED (red digits on dark) | 40% | Most common modern signs |
| Backlit (white panel) | 30% | Shell/Coles Express style |
| Digital (full color LCD) | 15% | Newer stations |
| Mechanical (flip digits) | 15% | Older stations, rarer |

### Conditions Distribution Target

| Condition | Min % | Notes |
|-----------|-------|-------|
| Day, clear | 50% | Baseline |
| Day, overcast | 20% | Common in Melbourne/Sydney |
| Night | 15% | LED glow, reflections |
| Rain | 10% | Droplets on lens |
| Dusk/dawn | 5% | Mixed lighting |

### Quality Metrics (Production Gate)

| Metric | Target | Measured On |
|--------|--------|-------------|
| Finder mAP50-95 | >0.85 | Real val set |
| Finder mAP50 | >0.95 | Real val set |
| Price Reader ExactMatch | >95% | Real crops |
| Price Reader CharAcc | >99% | Real crops |
| Label Reader ExactMatch | >90% | Real crops |
| Fuel type normalization | >95% | Fuzzy match accuracy |
| E2E: correct price extraction | >85% | Real test images |

---

## Versioning

Datasets are versioned: `finder_v1`, `finder_v2`, etc.

Each version is immutable once created. New data → new version.

Version changelog tracked in `docs/internal/DATA_INVENTORY.md`.

---

## Lessons from Thai ID Project

1. **Real data is the dominant lever.** 9 real crops → 0% CID valid. 561 crops → 33% valid. Synthetic alone plateaus.
2. **Overlap detection is critical.** 8 Roboflow datasets → only ~792 truly unique images. Always deduplicate.
3. **Visual validation is mandatory.** Statistics lie. Look at the actual images.
4. **Annotation format mismatches are silent killers.** YOLO polygon labels parse silently as wrong bboxes.
5. **Train/test contamination destroys evaluation.** Deduplicate before splitting.
