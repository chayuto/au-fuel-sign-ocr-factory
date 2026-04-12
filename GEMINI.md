# Gemini CLI: AU Fuel Sign OCR Factory

This project is a high-precision ML training pipeline for Australian fuel station price sign OCR, optimized for real-time mobile edge deployment (<15 MB total model budget).

## Project Overview

- **Goal:** Real-time detection and extraction of fuel prices from Australian petrol stations via mobile/dashcam.
- **Architecture:** A "Detect → Track → Crop → Read" pipeline:
    - **Finder (YOLO26n):** Detects the physical `sign_board` (pylon panel) at 640x640.
    - **Tracker (ByteTrack):** Follows the sign across frames.
    - **Row Detector (Classical CV):** Finds fuel rows on high-resolution crops from the original frame.
    - **Experts (CNN/CRNN):** Classifies brands and fuel types, and reads numeric prices (CTC).
- **Target Specs:** <15MB total size, <200ms full pipeline latency.
- **Tech Stack:** Python 3.11+, YOLO26 (Ultralytics), OpenCV, Albumentations, Pytest.

## Core Mandates & Conventions

- **Accuracy over Metrics:** Prioritize hand-verified, honest labels. Test set labels are sacred.
- **Validation First:** Every stage (Scrape → Label → Build → Train → Eval) must be verified before proceeding.
- **Experiment Logging:** Every training run MUST be documented in `docs/experiments/EXP-NNN_<name>.md`.
- **YOLO26 Only:** Do not use older YOLO versions. Always use `end2end=False` for validation and export.
- **Sign Board Definition (v7):** `sign_board` includes the full physical panel (brand + prices), excluding the pole and background.
- **No PII Concerns:** Fuel signs are public data.

## Development Workflows

### Environment Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,annotate]"
```

### Data Pipeline
- **Build Finder Dataset:**
  ```bash
  .venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42 --freeze-split <prior_manifest.json>
  ```
- **Validation/QA:** Use `scripts/draw_annotations.py` to verify label quality before training.

### Training & Evaluation
- **Train Finder:**
  ```bash
  PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
      data=data/finder/dataset.yaml model=yolo26n.pt \
      epochs=50 imgsz=640 batch=4 device=mps amp=False \
      freeze=10 mosaic=0.5 seed=42 \
      2>&1 | tee runs/finder/<exp_name>_train.log
  ```
- **Evaluate (Canonical Test v2):**
  ```bash
  PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
      data=data/finder_canonical_test_v2/dataset.yaml \
      model=<path>/weights/best.pt device=mps amp=False end2end=False
  ```

### Testing & Linting
- **Run Tests:** `pytest`
- **Linting:** `ruff check .`

## Key Directories

- `src/au_fuel_sign_ocr_factory/`: Core logic (synth, annotate, reader, utils).
- `scripts/`: CLI entry points for the data pipeline and training.
- `configs/`: Domain-specific enums (brands, fuel types, sign templates).
- `docs/experiments/`: Historical record of all ML experiments (EXP-NNN).
- `data/`: Local data storage (ingest, raw, finder, reader_experts).

## Agent Working Style

When working in this repo, adopt the **ML/AI Researcher** persona:
1. **Hypothesize:** State expectations before actions.
2. **Experiment:** Run minimal tests to validate hypotheses.
3. **Log:** Document everything in `docs/experiments/`.
4. **Analyze:** Compare results against hypotheses.
5. **Iterate:** Pivot based on findings.
