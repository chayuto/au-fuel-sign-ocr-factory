# Architecture Review — sign_board Redefinition (v7)

## What We're Changing and Why

### The Problem

sign_board was defined as "fuel rows only" — a tight box around just the LED price digits. This caused:

1. **Tiny detection target** (10-20% of pylon area) → mAP50 stuck at 0.40 on clean eval
2. **No brand context** in the crop → Brand Classifier can't work
3. **Inconsistent labeling** — agents disagreed on exact fuel row boundaries
4. **Bbox estimation errors** — Sonnet can't precisely estimate coordinates for a small, ambiguous region

### The Fix

**sign_board = the physical sign panel** — the rectangular face of the pylon that contains brand header + fuel price rows.

This is:
- A clear, unambiguous physical object
- Bigger target (30-50% of pylon) → easier to detect
- Includes brand logo → feeds Brand Classifier
- Structurally consistent across all Australian brands

## Updated Pipeline

```
Raw Camera Frame (640x640)
  → YOLO26n Finder (1 class: sign_board)
      → sign_board = physical sign panel (brand + fuel rows)
      → Crop sign_board region
  → Within the crop:
      → Brand Classifier (brand logo visible at top)    → "caltex"
      → Fuel row detection (either YOLO stage 2 or geometric)
          → For each fuel row:
              → Price Reader (CTC)                      → "189.9"
              → Fuel Type Classifier                    → "E10"
  → Validation (price range, fuel type normalization)
```

### Key Changes from Current Architecture

| Aspect | Before (v5/v6) | After (v7) |
|--------|---------------|------------|
| sign_board scope | Fuel rows only | Full sign panel (brand + rows) |
| Finder classes | Experiments tried 1-2 classes | **1 class only (sign_board)** |
| brand_zone | Separate class in JSON | **Retired** — included in sign_board |
| fuel_label / fuel_price | Detected by Finder YOLO | **Moved to stage 2** (within crop) |
| Brand Classifier input | sign_board crop (no brand visible) | sign_board crop (brand included) |

### What Does NOT Change

- **Downstream models** — Price Reader, Fuel Type Classifier, Brand Classifier architectures unchanged
- **Annotation schema** — JSON sidecar still stores all bbox classes for flexibility
- **Fuel types / brands** — same closed enums
- **Model budget** — still <15 MB total
- **Training recipe** — freeze=10, mosaic=0.5, 50 epochs confirmed optimal

## Impact on Existing Data

### 596 existing annotations need updating

**sign_board bbox must be expanded** to include the brand header panel above the fuel rows.

Options:
1. **Programmatic expansion** — use brand_zone bbox (where available) to expand sign_board upward. ~200 annotations have brand_zone.
2. **Re-label with Sonnet** — expensive (~$50 in API costs) but accurate
3. **Hybrid** — programmatic expansion + visual QA on worst cases

**Recommendation: Option 3.** Programmatically expand sign_board to include brand_zone, then visual QA the ones that look wrong.

### fuel_label and fuel_price annotations

These stay in the JSON sidecar but are **no longer used by the Finder**. The Finder only detects sign_board (1 class). fuel_price detection moves to a stage 2 model that operates on the sign_board crop.

This is actually a simplification — the Finder has ONE job: find the sign.

## Revised Finder Training Plan

### Immediate (EXP-021)

1. Expand existing sign_board bboxes to include brand header
2. Build 1-class dataset with expanded sign_boards
3. Train with confirmed recipe (freeze=10, mosaic=0.5, 50ep)
4. Evaluate on canonical test v2
5. Expected: mAP50 > 0.50 (bigger target = easier detection)

### If mAP50 improves significantly

The sign_board redefinition is validated. Continue the scrape+label+train loop with v7 rules.

### If mAP50 doesn't improve

The issue is elsewhere (annotation quality, data diversity, model capacity). Investigate further.

## Questions to Resolve Before Starting

1. **How far up should sign_board extend?**
   - To the brand logo panel? (most common)
   - To the very top of the physical pylon structure?
   - What about pylons where brand is physically separate from price panel?

2. **Should we keep annotating fuel_label/fuel_price in the JSON?**
   - Pro: flexibility for future stage 2 experiments
   - Con: extra labeling time, quality issues with small bbox estimation

3. **Do we need to re-scrape or is the current 596 enough for the first test?**
