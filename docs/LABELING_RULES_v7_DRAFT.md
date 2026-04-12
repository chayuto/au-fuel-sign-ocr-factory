# Labeling Rules v7 — DRAFT for Discussion

## The Problem with v5/v6

The v5 rule said: "sign_board covers ONLY the fuel rows, NOT the brand logo, NOT promo panels, NOT the pylon structure."

This created three problems:
1. **Tiny detection target** — a tight crop around just the fuel rows is ~10-20% of the pylon. Hard for YOLO to find.
2. **Inconsistent interpretation** — agents disagreed on what "fuel rows only" means. Some included promo rows ("Save 4c"), some didn't. Some included the bottom edge, some cut it off.
3. **No context for downstream** — a tight crop of just fuel rows gives the Price Reader no structural context (no brand, no sign edges, no background contrast).

## Proposed v7 Rule: sign_board = Physical Sign Face

**sign_board should cover the entire rectangular face of the price sign panel** — from the top of the first information panel to the bottom of the last fuel row, edge to edge horizontally.

### What to INCLUDE in sign_board:
- The brand header panel (e.g., "Caltex", "Woolworths" logo panel at top)
- All fuel type + price rows
- Promo panels that are physically part of the sign face (e.g., "Save 4c", "Discount Fuel Price")
- The physical edges/frame of the sign panel

### What to EXCLUDE from sign_board:
- The pylon pole/structure below or above the sign
- The sky/background
- Separate signs not physically attached (e.g., a separate "Car Wash" sign on the same pole)
- "bp ultimate" or "AMPLIFY" marketing panels that are clearly separate from the price panel

### Visual Guide

```
EXCLUDED (separate structure above)
┌─────────────────────┐
│    ★ CALTEX          │ ← INCLUDED (brand header on sign face)
│   ⓦ Woolworths       │ ← INCLUDED (co-brand on sign face)
├─────────────────────┤
│ Save 4c per litre   │ ← INCLUDED (promo panel on sign face)
├─────────────────────┤
│ Unleaded    145.9   │ ← INCLUDED (fuel row)
│ Unleaded    149.9   │ ← INCLUDED (fuel row)
│ Vortex DSL  127.9   │ ← INCLUDED (fuel row)
│ LPG          52.5   │ ← INCLUDED (fuel row)
└─────────────────────┘
    ║ pylon pole ║      ← EXCLUDED (structure)
```

**sign_board bbox** = the entire rectangle from Caltex logo to LPG row, edge to edge.

### Why This Is Better

1. **Bigger target** — easier for YOLO to detect (~30-50% of pylon vs ~10-20%)
2. **Consistent** — "the whole sign face" is unambiguous, unlike "just the fuel rows"
3. **Better crop for downstream** — the crop gives the Price Reader brand context, sign structure, and all fuel rows
4. **Matches human intuition** — when a person points at "the price sign," they point at the whole panel, not just the LED digits

### Impact on Existing Annotations

~596 existing annotations have "tight fuel rows" sign_boards. Options:
1. **Re-label all** — expensive but clean
2. **Keep as-is, label new ones with v7** — creates inconsistency
3. **Programmatic expansion** — expand existing sign_boards by a fixed margin to approximate v7

**Recommendation:** Option 3 for existing + v7 for all new labels. The margin expansion won't be perfect but it's 80% of the way there.

### Impact on Other Classes

- **brand_zone**: May become redundant if sign_board now includes the brand header. Consider retiring brand_zone.
- **fuel_label / fuel_price**: No change — these still mark individual rows within the sign.
- **Containment rule**: All fuel_label and fuel_price bboxes must still be INSIDE sign_board. With v7's wider sign_board, this is easier to satisfy.

## Questions for Discussion

1. Should we retire `brand_zone` class since sign_board now includes it?
2. Should we programmatically expand existing annotations or re-label?
3. What about signs where the brand header is physically separate from the price panel (e.g., BP with a separate "bp rewards" topper)?
