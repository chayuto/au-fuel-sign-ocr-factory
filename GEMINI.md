# Gemini CLI: AU Fuel Sign OCR Factory (The Gemini Way)

This document defines the foundational mandates and expert workflows for the AU Fuel Sign OCR Factory project.

## Project Identity & Constraints

- **Goal:** Real-time Australian fuel station price OCR for mobile edge deployment.
- **Budget:** <15 MB total for all models combined.
- **Latency:** <50ms detection, <200ms full read pipeline.
- **Architecture:** "Detect → Track → Crop → Read" (YOLO26n Finder → Classical CV Row Detection → Expert Readers).

## Core Mandates (The "Claude Way")

1.  **Data Integrity First:** Accurate labels are the foundation. Test set labels are sacred and hand-verified. Accept real metrics—never game evaluation.
2.  **3-Level Ingest Dedup:** Every new image must pass `process_ingest.py` (Filename, SHA-256, pHash) before entering `data/tmp/`.
3.  **v7 sign_board Definition:** In Stage 1 (Finder), `sign_board` = **Full Physical Sign Panel** (brand header through last fuel row). Exclude the pylon pole and background.
4.  **Vision Token Economics:** Use Sonnet for all visual QA and labeling. Image encoding cost dominates; model reasoning is secondary. Accuracy is the only optimization.
5.  **Mandatory Reconciliation:** Always run `reconcile_manifest.py` after labeling to fix manifest write-clobber and ensure disk truth (annotations) matches the CSV.
6.  **Experiment Logging:** Every training run MUST be documented in `docs/experiments/EXP-NNN_*.md` following the scientific method.
7.  **No Training Permitted:** The agent is strictly prohibited from executing any training commands (e.g., `yolo detect train`). All work must focus on data engineering, analysis, and classical CV refinement.
8.  **Visual Verification Mandate (2026-04-12 Failure):** NEVER guess or 'mentally simulate' labeling. Every image MUST be visually inspected by a vision-capable subagent (e.g., `generalist`) before annotation. A 0% yield is better than a 1% error rate. Aggressively skip non-AU, manufacturer, or non-fuel images.

## Lessons Learned: The 2026-04-12 Incident
- **Event:** Gemini agent labeled 12/12 garbage images (US gas stations, hospital signs, AC ads) as AU fuel signs.
- **Root Cause:** Failure to use vision tools; reliance on filename heuristics and 'guessing'.
- **Remediation:** Purged 100% of the batch. Established the 'Visual Verification Mandate'.

## Expert Workflows

### 1. Data Collection (Scrape Dispatch)
- **Proven Winners:** Use "Brand + Regional City" (e.g., "APCO Bendigo Victoria").
- **State+Brand:** Always include state + brand + "fuel price sign" to minimize international noise.
- **Filter:** Add `-manufacturer -alibaba -stock` to queries.

### 2. Ingest Pipeline
```bash
# Process and dedup images from data/ingest/ to data/tmp/
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py --phash-threshold 10
```

### 3. Stage 1 Labeling (Finder)
- **Goal:** 1 bbox (`sign_board`) per image.
- **Agent:** Sonnet (Combined screen + label in one pass).
- **Yield:** Expected 40-100% for state+brand queries.
- **Validation:** READ the preview image (`scripts/draw_annotations.py`) before marking done.

### 4. Training (YOLO26n)
- **Model:** `yolo26n.pt` only.
- **Recipe:** `freeze=10, mosaic=0.5, epochs=50, imgsz=640, batch=4`.
- **Observability:** Always pipe to `tee` and verify the first epoch within 60s.
- **Evaluation:** ALWAYS use `end2end=False` and `canonical_test_v2`.

## Key Directories
- `data/ingest/`: Ephemeral scrape drop-off (Git-tracked).
- `data/tmp/`: Gold labeling dataset (Gitignored).
- `docs/experiments/`: The sequential memory of the project (EXP-NNN).
- `scripts/`: CLI entry points for the entire pipeline.

## Agent Working Style: ML Researcher
- **Hypothesize:** State numeric expectations before actions.
- **Experiment:** Run minimal tests first.
- **Log:** Document everything (including failures).
- **Analyze:** Compare against scaling trends (e.g., +0.002 mAP/image).
- **Iterate:** Pivot based on findings.
