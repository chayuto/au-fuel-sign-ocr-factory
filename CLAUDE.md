# AU Fuel Sign OCR Factory

## Core Principle: Real-Data-First Edge OCR

Unlike Thai ID (PII-constrained, synthetic-first), fuel sign prices are public data. Prioritize real image collection; use synthetic data only for edge-case augmentation (night, rain, extreme angles, rare brands).

**Total model budget: <15 MB.** Single-pass YOLO Finder + lightweight Reader experts for mobile deployment.

## Agent Working Style: ML/AI Researcher

Work like a scientist. Every task follows the experimental method:

1. **Hypothesize** — State what you expect and why before writing code or running training
2. **Experiment** — Run the smallest test that can confirm or reject the hypothesis
3. **Log** — Record all configs, metrics, observations in `docs/experiments/EXP-NNN_*.md`
4. **Analyze** — Compare results against the hypothesis. Identify surprises.
5. **Iterate** — Update the hypothesis. Design the next experiment based on findings.

**Experiment log format:** `docs/experiments/EXP-NNN_<short_name>.md` with sections: Hypothesis, Setup, Results, Analysis, Next Steps, Reproducibility. Every training run gets a log entry.

**Naming convention:** `EXP-001`, `EXP-002`, etc. Sequential, never reused.

## Architecture: Finder → Price Reader + Fuel Type Classifier → Validator

```
Raw Camera Frame (640x640)
  → YOLO26n Finder (sign_board, fuel_price)
      → sign_board          → crop context
      → fuel_price(s)       → variable count (3-6 per sign)
  → For each fuel_price (sorted top→bottom by Y):
      → Crop price region   → Price Reader (CTC, numeric)    → "189.9"
      → Crop left-of-price  → Fuel Type Classifier (8-class) → "E10"
  → sign_board crop         → Brand Classifier (13-class)    → "shell"
  → Validation (price range, fuel type normalization)
```

**Key design decisions:**
- `fuel_price` has **variable instance count** (3-6 per sign). YOLO handles this naturally.
- Fuel type is **classification, not OCR** — only 8 canonical types. Crop derived geometrically: `[sign_board.x1, price.y1, price.x1, price.y2]`.
- No spatial pairing needed — label and price come from the same row by construction.
- All 4 annotation classes kept in JSON sidecar. Dataset builder selects Finder classes per experiment via `--classes`.

### Finder Classes (experiment-dependent)

Annotations always store all 4 classes. Training uses a subset:

| class_id | Name | Annotated | EXP-001 |
|----------|------|-----------|---------|
| 0 | `sign_board` | Always | Yes → 0 |
| 1 | `brand_zone` | When visible | No (use sign_board crop) |
| 2 | `fuel_label` | Always | No (use left-of-price geometry) |
| 3 | `fuel_price` | Always | Yes → 1 |

### Downstream Models

| Model | Input | Output | Architecture |
|-------|-------|--------|-------------|
| Price Reader | fuel_price crop | "189.9" | SimpleCRNN (CTC, `0-9.`) |
| Fuel Type Classifier | left-of-price crop | 1 of 8 types | SimpleCNN |
| Brand Classifier | sign_board crop | 1 of 13 brands | SimpleCNN |

### Model Budget

| Component | Estimate |
|-----------|----------|
| Finder YOLO26n INT8 | ~3 MB |
| Price Reader INT8 | ~1.5 MB |
| Fuel Type Classifier INT8 | ~0.5 MB |
| Brand Classifier INT8 | ~1 MB |
| **Total** | **~6 MB** |

## Project Structure

- `src/au_fuel_sign_ocr_factory/synth/` — Synthetic data generation (signs, LED digits, augmentation)
- `src/au_fuel_sign_ocr_factory/annotate/` — Real image annotation pipeline (schema, I/O, converter, cropper)
- `src/au_fuel_sign_ocr_factory/formats/` — YOLO annotation writer
- `src/au_fuel_sign_ocr_factory/reader/` — Reader training infrastructure (dataset, vocab, metrics)
- `src/au_fuel_sign_ocr_factory/utils/` — Font loading, spatial pairing
- `configs/` — Fuel types, brands, finder classes, reader experts, sign templates
- `scripts/` — CLI entry points for dataset generation, training, export
- `docs/experiments/` — Experiment logs (EXP-NNN format)

## Data Constitution

- **Fuel types:** Closed enum — U91, E10, P95, P98, Diesel, LPG, AdBlue, E85
- **Brands:** Shell, BP, Ampol, Caltex, 7-Eleven, United, Costco, Liberty, Puma, Metro, Mobil, OTR
- **Each sign** has 3-6 fuel entry rows, each with a label bbox + price bbox
- **Prices** in cents/litre, format XXX.X (e.g., 189.9), range 80.0–350.0

## Commands

```bash
# Setup
python -m pip install -e ".[dev]"

# Build Finder dataset (select classes per experiment)
.venv/bin/python scripts/build_finder_dataset.py --classes 0,3          # 2-class: sign_board + fuel_price
.venv/bin/python scripts/build_finder_dataset.py --classes 0,2,3        # 3-class: + fuel_label
.venv/bin/python scripts/build_finder_dataset.py --classes 0,1,2,3      # 4-class: all

# Tests
pytest

# Training — Finder (YOLO26 only — never yolo11)
# IMPORTANT: Always use device=mps amp=False on Apple Silicon.
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train data=data/finder/dataset.yaml model=yolo26n.pt epochs=100 imgsz=640 batch=16 device=mps amp=False

# Training — Price Reader (SimpleCRNN on Apple MPS)
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -u scripts/train_reader.py \
    --expert price --framework torch --data data/reader_experts/price \
    --output runs/reader/price_v1 --epochs 80 --batch-size 256 --lr 0.001

# Training — Fuel Type Classifier (SimpleCNN, 8 classes)
# TODO: script not yet written

# TFLite Export (requires separate Python 3.13 venv)
.venv-export/bin/python scripts/export_tflite.py reader --all
.venv-export/bin/python scripts/export_tflite.py summary
```

## Conventions

- Python 3.11+, type hints on public APIs
- All coordinates in normalized [0,1] space; resolution applied at render time
- Fuel types defined in `configs/fuel_types.yaml` — closed enum, single source of truth
- Finder classes defined in `configs/finder_classes.yaml` — 4 annotation classes, training subset selected via `--classes`
- **YOLO26 only** — never use yolo11 or older architectures
- **Experiment logs** — every training run gets `docs/experiments/EXP-NNN_*.md`
- **Visual QA mandatory** — every annotation must have a preview image (`data/tmp/preview/{stem}_preview.jpg`). Run `python scripts/draw_annotations.py` after any labeling or annotation update. Annotations without previews are not considered complete.
- **Subagent model selection** — use `model: "sonnet"` for labeling and scraping agents (mechanical visual work). Reserve Opus for planning, architecture, experiment analysis, and complex debugging.
- **Subagent concurrency** — max 5-8 parallel agents to avoid API rate limits. For labeling, use 1 image per agent for best quality (~300s, ~45K tokens each).
- Prices in Australian cents per litre, one decimal place (XXX.X)
- Fuel sign images are public data — no PII concerns, can share freely
