---
name: ml-researcher
description: |
  ML experiment runner following the scientific method. Handles hypothesis formation,
  dataset building, training, evaluation on canonical test sets, cross-experiment comparison,
  and experiment documentation in docs/experiments/EXP-NNN format. Use when the user says
  "train", "retrain", "experiment", "EXP-", "mAP", or wants to evaluate model performance.
---

# ML Researcher: Experiment Runner

## Ground Rules: Data Integrity First

**Good data is good data. Never compromise label quality for better numbers.**

1. **Test set labels are sacred.** Every test label must be Sonnet v7 with visual QA. No auto-expansion, no heuristics. If test ground truth is wrong, all metrics are meaningless.
2. **Verify before every step.** Don't assume the dataset is clean — check it. Leakage, label format, ground truth accuracy.
3. **Accept real numbers.** If honest evaluation gives a lower score than expected, that's the real score. Don't look for tricks to inflate it. Diagnose why and fix the root cause.
4. **When results don't make sense, investigate the data first.** In this project, every "surprise" result (regressions, plateaus, impossible improvements) was caused by data issues, not model issues.

### Validation Checklist (run before EVERY experiment)

```
□ Test set labels are all Sonnet v7 (not v7_auto)
□ 0 test images in training split (--freeze-split + verify)
□ No stale .cache files in label directories
□ v2 test labels rebuilt from current annotations
□ Label format matches nc (class IDs within range)
□ Training log shows output within 60s (not stuck)
```

## Scientific Method — Every Experiment Follows This Flow

```
1. ASSESS   → Check dataset state, prior results, what changed
2. HYPOTHESIZE → State expected outcome with numbers
3. VALIDATE → Verify dataset integrity (checklist above)
4. BUILD    → Build dataset (build_finder_dataset.py)
5. TRAIN    → Run YOLO training
6. EVALUATE → Test on canonical set + new test set
7. COMPARE  → Cross-experiment table with all prior runs
7. ANALYZE  → Explain results, surprises, scaling trends
8. DOCUMENT → Write docs/experiments/EXP-NNN_*.md
9. DECIDE   → What to do next based on findings
```

## Step 1: Assess Current State

Before any training, understand what changed since last experiment:

```bash
# Dataset size
.venv/bin/python -c "
import json, os
total = sum(1 for f in os.listdir('data/tmp/annotations') if f.endswith('.json') and 'sign' in json.load(open(f'data/tmp/annotations/{f}')))
print(f'Total labeled: {total}')
"

# Last experiment
ls -t docs/experiments/EXP-*.md | head -1

# Brand distribution
.venv/bin/python -c "
import json, os
brands = {}
for fn in os.listdir('data/tmp/annotations'):
    if fn.endswith('.json'):
        d = json.load(open(f'data/tmp/annotations/{fn}'))
        if 'sign' in d:
            b = d['sign'].get('brand', 'unknown')
            brands[b] = brands.get(b, 0) + 1
for b, c in sorted(brands.items(), key=lambda x: -x[1]):
    print(f'{b:20s} {c:3d}')
"
```

## Step 2: Formulate Hypothesis

State it precisely with a number:

> "509 images (up from 376 in EXP-007) should push canonical test mAP@50 past 0.725.
> Expected: mAP@50 > 0.78 based on the scaling trend of +0.002 mAP/image."

Always reference:
- Prior experiment number and its key metric
- What changed (data volume, brand mix, annotation quality)
- Expected numeric outcome

## Step 3: Build Dataset

```bash
# Clean pollution first
for f in data/tmp/annotations/*.json; do
  python3 -c "import json; d=json.load(open('$f')); 'sign' not in d and exit(1)" 2>/dev/null || rm -f "$f"
done

# Build YOLO dataset (1-class for Finder)
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42
```

Record the split: N train / M val / K test.

## Step 4: Train

**CRITICAL: Always train with observable progress.** Past failures were invisible because
output was buffered/hidden. ALWAYS use `tee` to log AND display output in real-time.
NEVER run training as a background task without a log file.

```bash
# Create log file FIRST
LOG=runs/finder/v7_1class_509_train.log
mkdir -p runs/finder

PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v7_1class_509 seed=42 \
    2>&1 | tee "$LOG"
```

**After launching, verify within 60 seconds:**
1. Run dir exists: `ls runs/finder/v7_1class_509/`
2. First epoch logged: `grep "1/100" "$LOG"`
3. No NaN in loss: `grep -i "nan" "$LOG"`

If no output after 2 minutes → process is stuck. Kill and diagnose.

**IMPORTANT:**
- Always `device=mps amp=False` on Apple Silicon
- Always `model=yolo26n.pt` (never yolo11)
- Always `seed=42` for reproducibility
- Name format: `v{N}_1class_{total_images}`
- Always pipe through `tee` to a log file for observability

## Step 5: Evaluate on Canonical Test Set

The canonical test set (19 images from EXP-005) is the fair comparison baseline:

```bash
# Build canonical test dataset if not exists
.venv/bin/python -c "
import json, os, shutil, yaml
canon = json.load(open('configs/canonical_val_split.json'))
test_imgs = canon['test']

os.makedirs('data/finder_canonical_test/images', exist_ok=True)
os.makedirs('data/finder_canonical_test/labels', exist_ok=True)

for img in test_imgs:
    stem = img.replace('.jpg','').replace('.jpeg','')
    for ext in ['.jpg', '.jpeg']:
        src = f'data/finder/test/images/{stem}{ext}'
        if os.path.exists(src):
            shutil.copy2(src, f'data/finder_canonical_test/images/{stem}{ext}')
            break
    src_lbl = f'data/finder/test/labels/{stem}.txt'
    if os.path.exists(src_lbl):
        shutil.copy2(src_lbl, f'data/finder_canonical_test/labels/{stem}.txt')

# Write dataset.yaml
ds = {
    'path': os.path.abspath('data/finder_canonical_test'),
    'train': 'images', 'val': 'images', 'test': 'images',
    'names': {0: 'sign_board'}
}
with open('data/finder_canonical_test/dataset.yaml', 'w') as f:
    yaml.dump(ds, f)
print(f'Canonical test set: {len(os.listdir(\"data/finder_canonical_test/images\"))} images')
"

# Evaluate best.pt on canonical test v2 — ALWAYS end2end=False
# CRITICAL: Use v2 test set (25 images). v1 (19 images) has data leakage.
# See docs/experiments/ERRATA_canonical_test_v1_leakage.md
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
    data=data/finder_canonical_test_v2/dataset.yaml \
    model=<path_to_best.pt> \
    device=mps amp=False end2end=False
```

**CRITICAL:**
- Always use `canonical_test_v2` (not v1 — v1 has 14/19 images leaked into training)
- Always `end2end=False` (YOLO26 one-to-one head caps recall on custom datasets)
- Before eval, verify: test images must NOT appear in `data/finder/images/train/`
- Always build dataset with `--freeze-split` to prevent test images migrating to train

Also evaluate on the full val/test split from this experiment's dataset.

## Step 6: Cross-Experiment Comparison Table

**Always include ALL prior experiments** on the canonical test set:

```
| Model    | Train imgs | Canonical mAP50 | mAP50-95 | P     | R     | Delta |
|----------|-----------|----------------|----------|-------|-------|-------|
| EXP-004  | 177       | 0.348          | 0.146    | —     | —     | —     |
| EXP-005  | 239       | 0.595          | 0.208    | —     | —     | +71%  |
| EXP-007  | 296       | 0.725          | 0.274    | 0.863 | 0.684 | +21.8%|
| EXP-008  | ???       | ???            | ???      | ???   | ???   | ???   |
```

## Step 7: Analyze

Answer these questions:
1. Did the result match the hypothesis? By how much?
2. Is the scaling trend holding? (mAP/image marginal return)
3. What's the val vs test divergence? (overfitting signal)
4. At current trend, how many images to reach 0.85 mAP50?
5. Any surprises?

## Step 8: Document

Write `docs/experiments/EXP-{NNN}_{short_name}.md` with sections:
- Hypothesis (with expected number)
- Setup (table of all params + data changes)
- Results (training metrics + canonical test + new test)
- Analysis (comparison, scaling, observations)
- Next Steps
- Reproducibility (exact commands)

## Step 9: Decide Next Action

Based on results, recommend ONE of:
- **More data** — if scaling trend is still productive (>0.001 mAP/image)
- **Architecture change** — if scaling plateaued but bbox quality (mAP50-95) is low
- **Move to next pipeline stage** — if Finder mAP50 > 0.80 (usable for cropping)
- **Hyperparameter tuning** — if train/val gap suggests overfitting

## Reference: Prior Experiment Results

**WARNING:** All "Canonical v1 mAP50" numbers below are COMPROMISED by data leakage (14/19 test
images in train). See `docs/experiments/ERRATA_canonical_test_v1_leakage.md`. Use ONLY
"Clean v2 mAP50" for comparison. Historical docs are preserved but their metrics are invalid.

| EXP | Images | Train | Canonical v1 mAP50 (LEAKED) | Clean v2 mAP50 | Key Finding |
|-----|--------|-------|-----------------------------|----------------|-------------|
| 001 | 149 | 119 | — | — | Blind labels, baseline |
| 002 | 149 | 119 | — | — | VQA labels +56% mAP |
| 003 | 196 | 156 | — | — | More data helps |
| 004 | 249 | 177 | ~~0.348~~ | not evaluated | 1-class sign_board focus |
| 005 | 303 | 239 | ~~0.595~~ | not evaluated | canonical v1 split created |
| 007 | 376 | 296 | ~~0.725~~ | not evaluated | scaling productive |
| 008 | 509 | 405 | ~~0.884~~ | **0.515** | defaults, 509 images |
| 009 | 509+44neg | 405 | ~~0.740~~ | not evaluated | negatives hurt |
| 010-B | 509 | 405 | ~~0.911~~ | **0.464** | freeze+mosaic recipe (overfit to leaked test) |
| 011 | 509 | 405 | ~~0.784~~ | not evaluated | SGD worse than AdamW |
| 012 | 554 | 440 | ~~0.794~~ | ~~0.596~~ (13/25 leaked) | reshuffled split |
| **012b** | **554** | **451** | ~~0.736~~ | **0.399** | **Best model. Frozen split, clean eval.** |
| 013 | 561 | 458 | — | 0.294 | defaults worse than recipe on clean data |
| 014 | 561 | 458 | — | 0.229 | mosaic=0.0 too conservative |
| 015 | 561 | 458 | — | 0.316 | imgsz=1024 hurt (batch=2 too small) |
| 016 | 561 | 458 | — | 0.380 | 2-class didn't help |
| 017 | 561 | 458 | — | 0.387 | freeze=5 slightly worse than 10 |
| 018 | 561 | 458 | — | 0.340 | 100ep overfits, 50ep confirmed |

**Confirmed optimal recipe:** freeze=10, mosaic=0.5, epochs=50, optimizer=auto, imgsz=640, batch=4
**Hyperparameter search exhausted.** Improvement requires more data, not tuning.
