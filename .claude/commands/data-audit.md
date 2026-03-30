# Data Audit — Dataset Quality Assessment

You are auditing a dataset for the AU Fuel Sign OCR Factory project. Apply skeptical, thorough analysis. Assume nothing — verify everything.

## When invoked, do ALL of the following:

### 1. Dataset Overview

Read the dataset directory and produce:

```
| Split | Images | Labels | Empty Labels | Orphans |
|-------|--------|--------|-------------|---------|
| train | ?      | ?      | ?           | ?       |
| val   | ?      | ?      | ?           | ?       |
| test  | ?      | ?      | ?           | ?       |
```

Check: format (JPEG/PNG), resolution distribution, file sizes, any corrupted files.

### 2. Annotation Health

For YOLO-format labels:
- Class distribution (how many of each: sign_board, brand_zone, fuel_label, fuel_price)
- Bbox bounds check (all values in [0,1], no degenerate boxes w<0.01 or h<0.01)
- Entry count per image (histogram: how many fuel_label / fuel_price per image)
- Label-price pairing: do label and price counts match per image?

### 3. Visual Validation (MANDATORY)

Randomly sample 10 images and visually inspect each:
- Are bounding boxes correctly placed?
- Are fuel types legible?
- Are prices readable?
- Image quality grade: A (clear) / B (moderate) / C (poor) / D (unusable)

### 4. Cross-Dataset Overlap

Check for duplicates:
- MD5 hash comparison with existing datasets in `data/`
- Filename pattern analysis (same source images?)
- Visual similarity check on suspicious matches

### 5. Report Template

Write to `docs/internal/DATA_AUDIT_<dataset_name>.md`:

```markdown
# Data Audit: <dataset_name>

**Date:** YYYY-MM-DD
**Source:** [URL or collection method]
**License:** [license]
**Location:** `data/<path>/`

## Summary
[1-2 sentence verdict: usable / partial / unusable]

## Dataset Structure
[table from step 1]

## Classes
[distribution table]

## Critical Issues
### 1. [BLOCKER/HIGH/MEDIUM/LOW]: [Issue]
[description]

## Quality Assessment
[visual validation results, grade distribution]

## Recommendations
[what to do with this dataset]
```

## Principles

- **Visual validation is non-negotiable.** You MUST look at actual images, not just statistics.
- **Fuel sign specific checks:** Prices should be XXX.X format, fuel types should match known Australian types, brand logos should be recognizable.
- **No PII concerns for fuel signs** — but check for accidental capture of license plates, faces, etc.
- **Document everything.** Future-you will thank present-you.
