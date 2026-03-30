# Labeling Guide -- AU Fuel Sign OCR

## Overview

This guide defines the annotation standards for the YOLO26n Finder model. Every real image must be labeled consistently to train a reliable detector. The Finder outputs 4 classes that feed downstream Reader experts and spatial pairing.

Reference schema: `src/au_fuel_sign_ocr_factory/annotate/schema.py`
Class definitions: `configs/finder_classes.yaml`

---

## 1. Class Definitions

| class_id | Name | What to annotate | Downstream use |
|----------|------|-------------------|---------------|
| 0 | `sign_board` | The rectangular fuel-price panel area of the pylon | Framing / crop region |
| 1 | `brand_zone` | Brand logo + name area at the top of the pylon | Brand Classifier |
| 2 | `fuel_label` | Each fuel-type text label (one per fuel row) | Label Reader (alphanumeric) |
| 3 | `fuel_price` | Each LED/printed price display (one per fuel row) | Price Reader (numeric) |

### Instance counts per image

| Class | Count | Notes |
|-------|-------|-------|
| `sign_board` | 1 | One per image (crop or select the primary sign) |
| `brand_zone` | 0-1 | May be absent if logo is cropped out or not visible |
| `fuel_label` | 3-6 | One per fuel row on the sign |
| `fuel_price` | 3-6 | One per fuel row, must pair 1:1 with labels |

---

## 2. Bounding Box Rules

All coordinates are **normalized [0, 1]** relative to image dimensions. YOLO format: `class_id cx cy w h`.

### 2.1 `sign_board` (class 0)

**Include:** The rectangular panel area containing all fuel entries (labels + prices). This is the "price section" of the pylon.

**Exclude:**
- Brand logo/name area above the price section
- Promotional banners ("save 4c", "Velocity Frequent Flyer", etc.)
- Non-fuel signage (Wild Bean Cafe, ATM, etc.)
- The pylon pole/structure below the sign

**Tight fit:** The bbox should tightly bound the price panel with minimal background. Include a ~2% padding on each side for detection margin.

```
Example — Coles Express pylon:

  ┌──────────────────────┐
  │   coles express      │  ← brand_zone (class 1)
  ├──────────────────────┤
  │   save 4c per litre  │  ← EXCLUDE (promo, not fuel entry)
  ├──────────────────────┤
  │  Unleaded E10  139.9 │ ┐
  │  Unleaded      141.4 │ │
  │  V-Power       164.9 │ ├─ sign_board (class 0)
  │  Diesel        136.9 │ │
  │  Autogas        78.9 │ ┘
  └──────────────────────┘
```

### 2.2 `brand_zone` (class 1)

**Include:** The brand logo, brand name text, and any brand-specific background panel at the top of the pylon.

**Tight fit:** Bound the brand area tightly. If the brand logo sits inside a colored panel, include the panel.

**When to omit:**
- Brand is not visible (cropped, obscured, night with no illumination)
- Image is a tight crop of only the price section

### 2.3 `fuel_label` (class 2)

**Include:** The text identifying the fuel type on each row. This is the alphanumeric label on the left side of each fuel entry.

**Tight fit:** Bound only the text characters. Do not include excess background on left/right.

**Label text examples:**
- `Unleaded E10`, `Unleaded`, `Unleaded 91`
- `V-Power`, `V-Power Racing`
- `Premium 95`, `Premium 98`, `P95`, `P98`
- `Diesel`, `Ultimate Diesel`, `Vortex Diesel`
- `LPG`, `Autogas`, `Auto LPG`
- `AdBlue`
- `E85`

**Include brand-specific naming:** If the sign says "Ultimate 98" (BP) or "Amplify Premium" (Ampol), label what's on the sign -- the Reader will handle normalization.

### 2.4 `fuel_price` (class 3)

**Include:** The LED digit display area showing the price for each fuel row. This is typically on the right side.

**Tight fit:** Bound the LED digit area including all digits and the decimal point. Do not include the label text or excess panel background.

**Format:** Prices are in cents per litre, displayed as `XXX.X` (3 digits + decimal + 1 digit). Occasionally `XX.X` for cheap fuels (LPG).

**Decimal point:** The `.` (decimal point) is typically a small LED dot between the 3rd and 4th digit. Ensure it is within the bbox.

**Trailing `.9`:** Almost all AU fuel prices end in `.9`. The small superscript `9` after the decimal may sit slightly higher than the main digits. Include it in the bbox.

---

## 3. Row Pairing Rule

Each `fuel_label` must pair with exactly one `fuel_price` on the same horizontal row. The pairing is done by Y-coordinate proximity (see `utils/pairing.py`).

**Critical:** If a row has a label but the price is unreadable/off/blank, do NOT annotate that row. Both label and price must be visible to be a valid annotation pair.

---

## 4. Edge Cases

### 4.1 Promotional banners / non-fuel rows

Signs often include "Save 4c per litre" (Coles/Woolworths), "Velocity Frequent Flyer" (BP), or "Pie Face" branding. **Do not annotate these as fuel entries.** They are neither `fuel_label` nor `fuel_price`.

### 4.2 Placeholder prices (999.9, 000.0, blank)

New or inactive stations sometimes display `999.9` or `000.0` or have blank LED panels.

- **999.9 or 000.0:** Annotate the bbox normally but add `"placeholder": true` in metadata. These are valid for Finder training (the model learns to detect the location) but should be excluded from Reader training data.
- **Blank/off LEDs:** Do not annotate that row.

### 4.3 Partially obscured signs

If tree branches, poles, or other objects partially cover the sign:
- **>70% visible:** Annotate normally. The model should learn to detect partially occluded signs.
- **<70% visible:** Skip the entire image. Not worth training on.
- Individual rows: If a specific row's price is >50% occluded, skip that row's label+price pair.

### 4.4 Multiple signs in one image

If a wide shot captures multiple pylon signs (e.g., two competing stations across a road):
- **Preferred:** Crop the image to focus on one sign, then annotate.
- **If uncropped:** Annotate only the **largest/most prominent** sign. Ignore distant or tiny signs.

### 4.5 Non-pylon price displays

Some stations display prices on canopy fascias, pump-top screens, or window stickers rather than pylon signs.
- **Canopy fascia signs:** Annotate normally -- same 4-class schema applies.
- **Pump-top small screens:** Skip -- too small for Finder at 640px input.
- **Window stickers / paper signs:** Skip -- not the target domain.

### 4.6 Night / low light

Night images with illuminated LED signs are high-value training data. Annotate normally. The LED digits are typically brighter and easier to read at night.

### 4.7 Angled / perspective views

Real-world camera angles mean signs are rarely perfectly frontal. Annotate the bounding box as it appears in the image (axis-aligned rectangle enclosing the visible sign area). YOLO handles perspective naturally.

### 4.8 Watermarked images (Alamy, stock)

Some web-sourced images have watermarks. Annotate normally -- the watermark adds noise that can be useful for model robustness. Flag `"watermarked": true` in metadata.

### 4.9 Historical / non-LED signs

Older mechanical flip-digit or printed signs follow the same schema. Use `sign_type: "mechanical"` or `sign_type: "backlit"` in metadata. The Finder still needs to detect them.

### 4.10 Discount overlays

"Save 4c" or "Shopper Docket" callouts on the sign panel:
- If the overlay occupies its own row/section separate from fuel entries, exclude it from `sign_board`.
- If the discount amount is embedded within a fuel entry row (rare), include it in that row's `fuel_label` bbox.

---

## 5. Annotation Metadata

Beyond YOLO bbox labels, each image gets a JSON sidecar (see `FuelSignAnnotation.to_dict()`) capturing:

```json
{
  "image": {
    "file": "au_fuel_wiki_coles_express_prices_wallsend.jpg",
    "source": "web",
    "conditions": {
      "time_of_day": "day",
      "weather": "clear"
    }
  },
  "sign": {
    "bbox": [0.15, 0.22, 0.85, 0.95],
    "brand": "shell",
    "sign_type": "led",
    "brand_bbox": [0.15, 0.02, 0.85, 0.20]
  },
  "entries": [
    {
      "fuel_type": "E10",
      "display_text": "Unleaded E10",
      "price": 139.9,
      "label_bbox": [0.16, 0.35, 0.45, 0.42],
      "price_bbox": [0.55, 0.35, 0.84, 0.42]
    }
  ]
}
```

### Required fields

| Field | Type | Notes |
|-------|------|-------|
| `file` | string | Filename relative to dataset root |
| `source` | enum | `manual`, `streetview`, `web`, `synthetic` |
| `brand` | string | Key from `configs/brands.yaml` (e.g., `shell`, `bp`) |
| `sign_type` | enum | `led`, `mechanical`, `backlit`, `digital` |
| `sign_bbox` | [x1,y1,x2,y2] | Normalized coordinates of sign_board |
| `entries[].fuel_type` | enum | Canonical ID from `configs/fuel_types.yaml` |
| `entries[].display_text` | string | Exact text as displayed on sign |
| `entries[].price` | float | Price in cents/litre (e.g., 189.9) |
| `entries[].label_bbox` | [x1,y1,x2,y2] | Normalized label bbox |
| `entries[].price_bbox` | [x1,y1,x2,y2] | Normalized price bbox |

### Optional fields

| Field | Type | Notes |
|-------|------|-------|
| `brand_bbox` | [x1,y1,x2,y2] | Brand zone bbox (omit if not visible) |
| `conditions.time_of_day` | enum | `day`, `night`, `dusk` |
| `conditions.weather` | enum | `clear`, `overcast`, `rain` |
| `placeholder` | bool | True if prices are 999.9 / inactive |
| `watermarked` | bool | True if image has stock watermark |
| `notes` | string | Free-text for edge case documentation |

---

## 6. Quality Checklist

Before submitting an annotation, verify:

- [ ] `sign_board` bbox tightly covers the price panel area only
- [ ] `brand_zone` bbox covers the logo/brand area (if visible)
- [ ] Every `fuel_label` has a matching `fuel_price` on the same row
- [ ] Label and price bboxes do not overlap each other
- [ ] No promo banners or non-fuel rows are labeled as fuel entries
- [ ] `fuel_type` maps to a valid canonical ID from `fuel_types.yaml`
- [ ] `display_text` matches what is actually written on the sign
- [ ] `price` value matches the LED digits (or is flagged as placeholder)
- [ ] Metadata `brand`, `sign_type`, `source` are filled correctly
- [ ] Partially occluded rows are either annotated (>50% visible) or skipped

---

## 7. File Organization

```
data/
  raw/
    batch_001/                    # One batch per collection session
      images/
        IMG_0001.jpg
        IMG_0002.jpg
      labels/                     # YOLO format .txt files
        IMG_0001.txt
        IMG_0002.txt
      annotations/                # Rich JSON sidecar files
        IMG_0001.json
        IMG_0002.json
      source_manifest.json        # Provenance tracking
  finder/                         # Generated YOLO dataset (train/val/test split)
    dataset.yaml
    train/images/
    train/labels/
    val/images/
    val/labels/
  reader_experts/                 # Cropped regions for Reader training
    price/
      images/
      labels.csv                  # filename,text
    label/
      images/
      labels.csv
```

---

## 8. Visual Reference

### Typical AU fuel sign anatomy

```
┌─────────────────────────────────┐
│         BRAND LOGO              │  ← brand_zone (class 1)
│         Brand Name              │
├─────────────────────────────────┤
│  [promo banner if any]          │  ← SKIP (not fuel entry)
├─────────────────────────────────┤
│  fuel_label_1    fuel_price_1   │ ┐
│  ─────────────   ─────────────  │ │
│  fuel_label_2    fuel_price_2   │ │ sign_board (class 0)
│  ─────────────   ─────────────  │ │
│  fuel_label_3    fuel_price_3   │ │
│  ─────────────   ─────────────  │ │
│  fuel_label_4    fuel_price_4   │ ┘
└─────────────────────────────────┘
         │
         │ (pylon pole - exclude)
         │
```

### LED digit display patterns

| Brand | LED Color | Background |
|-------|----------|------------|
| Shell / Coles Express | Red | Dark/Black panel |
| BP | Green | Green panel |
| Ampol | White/Red | Dark blue panel |
| United | Red | Blue panel |
| Caltex | White/Red | Red or white panel |
| 7-Eleven | Red/Orange | Green/White panel |
| Liberty | Red/Amber | Dark blue panel |
| Puma | Red/Amber | Dark panel |
| Mobil | Red | Blue panel |

### Price format

```
Standard:   1 8 9 . 9    (3 digits + decimal + 1 digit)
LPG/cheap:    7 8 . 9    (2 digits + decimal + 1 digit)
High:       2 4 9 . 9    (3 digits + decimal + 1 digit)
Superscript:  189⁹        (small 9 after decimal, slightly raised)
```
