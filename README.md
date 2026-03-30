# AU Fuel Sign OCR Factory

ML training pipeline for Australian fuel station price sign OCR, optimized for mobile edge deployment (<15 MB, real-time inference).

## Architecture

Single-pass YOLO26n Finder detects sign regions → Reader experts extract text → Validator normalizes and validates.

```
Camera Frame (640×640)
  → YOLO26n Finder (4 classes: sign_board, brand_zone, fuel_label, fuel_price)
  → Spatial Pairing (match labels ↔ prices by row)
  → Price Reader (numeric OCR) + Label Reader (alphanumeric OCR)
  → Fuel type normalization + price validation
  → Structured JSON output
```

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Extracted Fields

| Field | Example | Source |
|-------|---------|--------|
| Brand | Shell | Brand classifier |
| Fuel Type | U91, E10, P95, P98, Diesel, LPG | Label reader → enum normalization |
| Price (c/L) | 189.9 | Price reader |
