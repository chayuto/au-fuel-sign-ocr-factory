# AU Fuel Sign OCR Factory

## Product Goal

**A mobile app / dashcam system that reads Australian fuel station prices in real-time.**

Driving past a petrol station, the system:
1. Detects the fuel price sign board (the physical pylon panel)
2. Tracks it across frames as the car approaches
3. Picks the best frame (largest, sharpest view)
4. Reads all fuel prices from the sign
5. Outputs: "Shell — U91: 189.9, Diesel: 179.9, E10: 185.9"

**Constraints:**
- Runs on-device (mobile phone or dashcam hardware)
- Total model budget: **<15 MB** (all models combined)
- Real-time: <50ms per frame for detection, <200ms for full read
- Australian fuel stations only (15+ brands, XXX.X cents/litre format)

## Core Principles

### 1. Accurate Data Over Good Numbers

**Good data is good data. No shortcuts.** Never relax label quality to get better metrics. If accurate labels produce lower numbers, those are the real numbers — build from there.

- **Test set labels are sacred.** Every test label must be hand-verified by vision. No auto-expansion, no heuristics, no programmatic shortcuts on test data.
- **Training labels must be as accurate as possible.** Sonnet v7 with visual QA, not blind heuristics.
- **Accept real metrics.** If honest evaluation gives mAP50=0.50, that's the truth. Don't game the evaluation to inflate numbers.
- **The goal is a working product**, not a paper with impressive metrics. A dashcam that actually reads fuel prices.

### 2. Step-by-Step Validation

Every stage of the pipeline must be verified before proceeding to the next:

1. **Scrape** → verify images are AU fuel stations (not manufacturer renders, not non-AU)
2. **Label** → verify bbox is on the physical sign panel (READ the preview, every time)
3. **Build dataset** → verify 0 leakage (test images NOT in train), verify label format (class IDs match nc)
4. **Train** → verify training started (check log within 60s), verify no NaN loss
5. **Evaluate** → verify test set ground truth is accurate, verify end2end=False, verify no cache staleness
6. **Compare** → verify same test set, same ground truth, same evaluation settings across experiments

**If any step fails verification, STOP and fix it before continuing.** Proceeding with unverified data compounds errors — we learned this the hard way with data leakage (EXP-004–011) and noisy test labels (EXP-021c vs 021d).

### 3. Real-Data-First Edge OCR

Fuel sign prices are public data — no PII concerns. Prioritize real image collection over synthetic data. Use synthetic only for edge-case augmentation (night, rain, extreme angles, rare brands).

## Agent Working Style: ML/AI Researcher

Work like a scientist. Every task follows the experimental method:

1. **Hypothesize** — State what you expect and why before writing code or running training
2. **Experiment** — Run the smallest test that can confirm or reject the hypothesis
3. **Log** — Record all configs, metrics, observations in `docs/experiments/EXP-NNN_*.md`
4. **Analyze** — Compare results against the hypothesis. Identify surprises.
5. **Iterate** — Update the hypothesis. Design the next experiment based on findings.

**Experiment log format:** `docs/experiments/EXP-NNN_<short_name>.md` with sections: Hypothesis, Setup, Results, Analysis, Next Steps, Reproducibility. Every training run gets a log entry.

**Naming convention:** `EXP-001`, `EXP-002`, etc. Sequential, never reused.

## Architecture: Detect → Track → Crop → Read

```
Camera Feed (1080p / 720p, continuous)
  │
  ├─ Every frame (or every 3rd frame):
  │   → Resize to 640x640
  │   → YOLO26n Finder (1 class: sign_board)
  │   → Tracker (ByteTrack): follow sign across frames
  │
  ├─ When tracked sign reaches peak size in frame:
  │   → Crop from ORIGINAL resolution (not 640px)
  │   → This gives ~300x400px crop vs ~80x100 at 640px
  │
  └─ On the high-res crop:
      → Brand Classifier (top region of crop)       → "shell"
      → Row detection (classical CV, not ML)         → find fuel rows
      → For each row:
          → Right half → Price Reader (CTC)          → "189.9"
          → Left half  → Fuel Type Classifier        → "E10"
      → Validation (price range, fuel type normalization)
```

### Why This Architecture

1. **Detect at 640px, read at 1080p.** YOLO runs fast at low res. Price reading needs high res. Crop from original gives 4-10x more pixels on the digits.

2. **Track, don't re-detect.** Once the sign is found, ByteTrack follows it across frames for free (~1ms). No need to re-run YOLO every frame.

3. **Pick the best frame.** The sign grows as you approach. Read prices when the sign is largest and sharpest, not when it's tiny and distant.

4. **Classical CV for row detection.** Australian fuel signs have rigid horizontal structure. Horizontal projection + peak detection finds rows without any ML or annotations. This eliminates the need to annotate fuel_price/fuel_label bboxes for the Finder.

5. **1-class Finder.** The Finder has ONE job: find the physical sign panel. Everything else happens on the crop. Simpler model, simpler annotations, better detection.

### sign_board Definition (v7)

**sign_board = the physical sign panel** — the rectangular face containing the brand header and fuel price rows.

```
INCLUDE in sign_board:
┌─────────────────────┐ ←─┐
│    ★ CALTEX          │   │
│   ⓦ Woolworths       │   │ sign_board bbox
│ Save 4c per litre   │   │ (the whole panel face)
│ Unleaded    145.9   │   │
│ Diesel      127.9   │   │
│ LPG          52.5   │   │
└─────────────────────┘ ←─┘

EXCLUDE from sign_board:
    ║ pylon pole ║         ← structural support, not sign face
    separate signs nearby  ← car wash, ATM, etc.
    sky / background       ← only the physical panel
```

**Why the full panel, not just fuel rows:**
- Bigger, more structural detection target → easier for YOLO
- Includes brand logo → Brand Classifier works on the crop
- Unambiguous — "the sign face" is a clear physical object
- Consistent across all Australian brands

### Component Models

| Component | Input | Output | Architecture | Size |
|-----------|-------|--------|-------------|------|
| **Finder** | 640x640 frame | sign_board bbox | YOLO26n | ~3 MB |
| **Tracker** | bbox sequence | tracked ID | ByteTrack | ~0 (algorithm) |
| **Row Detector** | sign crop | row boundaries | Classical CV | ~0 (no ML) |
| **Price Reader** | row right-half crop | "189.9" | SimpleCRNN (CTC) | ~1.5 MB |
| **Fuel Type** | row left-half crop | "E10" | SimpleCNN (8-class) | ~0.5 MB |
| **Brand** | sign top region | "shell" | SimpleCNN (15-class) | ~1 MB |
| **Total** | | | | **~6 MB** |

### Current Focus: Finder

The Finder is the foundation. If it can't find the sign, nothing else works. Current status:
- 596 labeled images, mAP50=0.517 on clean test (25 images)
- **Annotation rework needed:** sign_board must be expanded from "fuel rows only" to "full sign panel" (v7)
- Training recipe confirmed: freeze=10, mosaic=0.5, 50 epochs, optimizer=auto
- Evaluation: always `end2end=False`, always canonical_test_v2 (25 images, verified 0 leakage)

## Project Structure

- `src/au_fuel_sign_ocr_factory/synth/` — Synthetic data generation
- `src/au_fuel_sign_ocr_factory/annotate/` — Annotation pipeline (schema, I/O, converter)
- `src/au_fuel_sign_ocr_factory/formats/` — YOLO annotation writer
- `src/au_fuel_sign_ocr_factory/reader/` — Reader training infrastructure
- `src/au_fuel_sign_ocr_factory/utils/` — Font loading, spatial pairing
- `configs/` — Fuel types, brands, finder classes, sign templates
- `scripts/` — CLI entry points
- `docs/experiments/` — Experiment logs (EXP-NNN format)
- `docs/research/` — External research references (YOLO26 training guide, etc.)

## Data Constitution

- **Fuel types:** Closed enum — U91, E10, P95, P98, Diesel, LPG, AdBlue, E85
- **Brands:** Shell, BP, Ampol, Caltex, 7-Eleven, United, Costco, Liberty, Puma, Metro, Mobil, OTR, APCO, EG, independent
- **Prices** in Australian cents per litre, format XXX.X (e.g., 189.9), range 80.0–350.0

## Commands

```bash
# Setup
python -m pip install -e ".[dev]"

# Build Finder dataset (1 class: sign_board)
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42 \
    --freeze-split <prior_manifest.json>

# Training — Finder (confirmed recipe)
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=50 imgsz=640 batch=4 device=mps amp=False \
    freeze=10 mosaic=0.5 seed=42 \
    2>&1 | tee runs/finder/<name>_train.log

# Evaluate — ALWAYS end2end=False, ALWAYS canonical_test_v2
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
    data=data/finder_canonical_test_v2/dataset.yaml \
    model=<path>/weights/best.pt device=mps amp=False end2end=False

# Tests
pytest
```

## Conventions

- Python 3.11+, type hints on public APIs
- All coordinates in normalized [0,1] space
- Fuel types defined in `configs/fuel_types.yaml` — closed enum
- **YOLO26 only** — never use yolo11 or older architectures
- **YOLO26 eval/export: `end2end=False`** — default `end2end=True` has artificial recall ceiling on custom datasets
- **Training observability** — always pipe through `tee <logfile>`, verify within 60s
- **Experiment logs** — every training run gets `docs/experiments/EXP-NNN_*.md`
- **Visual QA mandatory** — every annotation must have a preview image
- **Dataset integrity** — always use `--freeze-split`, always verify 0 leakage before training
- **sign_board = physical sign panel** (v7) — includes brand header + fuel rows, excludes pole/structure
- **1-class Finder only** — do NOT annotate fuel_price/fuel_label for the Finder. Row detection is classical CV on the crop.
- Fuel sign images are public data — no PII concerns
