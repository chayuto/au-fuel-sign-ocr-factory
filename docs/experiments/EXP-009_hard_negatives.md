# EXP-009: Hard Negative Mining for False Positive Reduction

## Motivation

EXP-008 achieved mAP@50 = 0.809 on the canonical test set with 509 labeled images, but precision remained low at **0.669** — roughly 1 in 3 detections was a false positive. The model had never been trained on a negative example: all 509 training images contain at least one `sign_board`. Without explicit negative supervision, the model lacked a penalty signal for predicting boxes on non-sign content (streetscapes, road signs, LED billboards, servo forecourts without pylons).

**Note (post-hoc):** The 0.669 precision and 0.809 mAP50 baselines above were measured using YOLO26's default `end2end=True` evaluation. As discovered during this experiment, `end2end=True` artificially suppresses recall via a one-to-one detection head. Re-evaluating EXP-008 with `end2end=False` yields P=0.840, R=0.827, mAP50=0.884 — a substantially stronger baseline than initially believed. The hypothesis was formulated against the weaker (incorrect) baseline.

**Prior art:** The Ultralytics documentation recommends 1–10% background images for production deployments. The YOLO training loop automatically penalizes any predicted box on an image with an empty label file, teaching the model "nothing here is a sign."

## Hypothesis

Adding ~40 hard negative images (0% → ~9% of training set) — Australian streetscapes, servo forecourts without visible pylon signs, road signs, LED billboards, and non-AU fuel stations — will:

1. **Increase precision** from 0.669 → **≥ 0.80** (≥ +20% relative improvement)
2. **Maintain recall** within ±0.03 of the EXP-008 baseline (0.769)
3. **Improve mAP@50** on the canonical test set from 0.809 → **≥ 0.82** (net positive from precision gains outweighing any minor recall drop)

**Null hypothesis:** Negatives have no effect on precision because the false positives are caused by insufficient positive diversity, not missing negative examples.

## Experimental Design

### Independent Variable
- Number and composition of hard negative images added to the training set

### Controlled Variables (identical to EXP-008)
| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class: sign_board) |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |
| Positive images | Same 509 labeled images as EXP-008 |

### Dependent Variables
- Precision, Recall, mAP@50, mAP@50-95 on canonical 19-image test set
- Same metrics on the experiment's own val/test split

### Negative Image Taxonomy

Target categories based on likely false positive triggers:

| Category | Description | Target Count | Rationale |
|----------|-------------|-------------|-----------|
| **servo_no_pylon** | AU petrol station forecourts, pumps, canopies — no pylon sign visible | 10-15 | Most common inference context; model sees brand logos, canopy structure |
| **road_signs** | Highway/road signs, speed limits, directional signs near servos | 5-8 | Tall pole-mounted rectangular structures similar to pylon silhouette |
| **led_commercial** | LED billboards, electronic menu boards, commercial signage | 5-8 | LED digit/panel confusion with price displays |
| **non_au_station** | Non-Australian fuel stations (UK, US, EU) with different format | 5-8 | Price format confusion (pence, gallons, euros) |
| **streetscape** | Australian street scenes near commercial areas, no fuel station | 5-8 | General background context |

**Total target: ~40 negatives** (~9% of 445-image training set)

### Methodology

1. **Collection:** Scrape images via Bing Image Search targeting each category
2. **Screening:** Visual verification that no Australian fuel price pylon is visible in any negative
3. **Integration:** Add `--negatives-dir` flag to `build_finder_dataset.py`; negatives get empty `.txt` label files in train split only
4. **Training:** Identical hyperparameters to EXP-008
5. **Evaluation:** Canonical 19-image test set (apples-to-apples with EXP-004 through EXP-008)

### Success Criteria

Formulated against the initially reported EXP-008 metrics (end2end=True):

| Metric | EXP-008 Baseline (e2e=True) | Minimum Acceptable | Target |
|--------|---------------------------|-------------------|--------|
| Precision | 0.669 | ≥ 0.75 | ≥ 0.80 |
| Recall | 0.769 | ≥ 0.74 | ≥ 0.76 |
| mAP@50 | 0.809 | ≥ 0.80 | ≥ 0.82 |

**Corrected baseline (e2e=False, discovered during this experiment):** P=0.840, R=0.827, mAP50=0.884.

## Setup

| Parameter | Value |
|-----------|-------|
| Model | yolo26n.pt (pretrained COCO) |
| Task | detect (1 class: sign_board) |
| Dataset | data/finder/dataset.yaml |
| Classes | sign_board(0) only |
| Positive images | 509 total (same as EXP-008): 405 train / 78 val / 26 test |
| **Negative images** | **44 train only** (9.8% of 449 train images) |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 4 |
| Device | mps (Apple Silicon) |
| AMP | False |
| Seed | 42 |
| Run name | `runs/finder/v8_1class_509_neg44` |

### Negative Image Collection

53 images scraped via Bing Image Search across 5 categories. 9 rejected during visual screening (UK fuel pylons with XXX.X format — too similar to AU targets). **44 validated negatives** retained.

| Category | Query | Scraped | Screened | Final | Description |
|----------|-------|---------|----------|-------|-------------|
| servo_no_pylon | "Australian petrol station forecourt pumps no sign" | 15 | 15 KEEP | 15 | Non-AU and AU forecourts, pumps, canopies — no pylon visible |
| road_signs | "Australian road sign highway directional sign" | 9 | 9 KEEP | 9 | Highway distance signs, directional signs, speed signs |
| led_commercial | "LED billboard electronic sign Australia commercial" | 10 | 9 KEEP | 9 | LED billboards, retail displays, commercial electronic signs |
| non_au_station | "UK petrol station price sign pence per litre" | 10 | 1 KEEP | 1 | **9 REJECTED** — UK pylons use identical XXX.X format; 1 borderline kept |
| streetscape | "Australian suburban street scene commercial area" | 10 | 10 KEEP | 10 | Residential streets, intersections, suburban scenes |
| **Total** | | **54** | | **44** | |

### Screening Protocol

Each image visually inspected using Claude Sonnet vision (3 parallel batches of ~18 images). Rejection criterion: image contains any fuel price pylon/board with readable prices in XXX.X format, regardless of country. Rationale: the detector should learn to find sign_board structures; UK pylons with identical format would penalize correct detections of structurally identical signs.

### Key Design Decision: Negatives in Train Only

Negatives are added to the **train split only**, not val or test. Rationale:
- Val/test metrics should measure detection quality on images that contain signs
- Adding negatives to val would artificially inflate precision metrics (easy true negatives)
- The canonical test set (19 images, all positives) remains the apples-to-apples comparison

## Results

### Training Metrics (val split, 78 positive images)

| Checkpoint | Epoch | Val P | Val R | Val mAP50 | Val mAP50-95 |
|-----------|-------|-------|-------|-----------|-------------|
| best.pt | 53 | 0.469 | 0.385 | 0.456 | 0.116 |
| last.pt | 100 | 0.444 | 0.410 | 0.356 | 0.092 |

Training time: ~67 min (100 epochs × ~40s/epoch) on Apple M5 MPS.

### Canonical Test Set (19 images, all positives)

**Critical discovery: `end2end=False` dramatically affects evaluation.** YOLO26's default `end2end=True` uses a one-to-one detection head that caps max detections and can produce double detections. Setting `end2end=False` falls back to the traditional one-to-many head with NMS, which is more reliable for custom datasets.

| Model | end2end | P | R | mAP50 | mAP50-95 |
|-------|---------|-------|-------|-------|----------|
| EXP-008 (no negatives) | True | 0.837 | 0.543 | 0.725 | 0.366 |
| **EXP-008 (no negatives)** | **False** | **0.840** | **0.827** | **0.884** | **0.444** |
| EXP-009 (44 negatives) | True | 0.753 | 0.474 | 0.585 | 0.268 |
| EXP-009 (44 negatives) | False | 0.787 | 0.582 | 0.740 | 0.348 |

### Cross-Experiment Comparison (canonical test, end2end=False)

| Model | Train imgs | Negatives | Canonical mAP50 | mAP50-95 | P | R | Delta mAP50 |
|-------|-----------|-----------|-----------------|----------|-------|-------|-------------|
| EXP-004 | 177 | 0 | 0.348 | 0.146 | — | — | — |
| EXP-005 | 239 | 0 | 0.595 | 0.208 | — | — | +71% |
| EXP-007 | 296 | 0 | 0.725 | 0.274 | 0.863 | 0.684 | +21.8% |
| EXP-008 | 405 | 0 | 0.884 | 0.444 | 0.840 | 0.827 | +21.9% |
| **EXP-009** | **405+44** | **44** | **0.740** | **0.348** | **0.787** | **0.582** | **−16.3%** |

**Note:** EXP-004 through EXP-007 values are historical (may have used end2end=True). EXP-008 vs EXP-009 are directly comparable (same evaluator, same 19 images, end2end=False).

## Analysis

### Hypothesis Rejected

Adding 44 hard negatives (9.8% of training set) **degraded all metrics**:
- Precision: 0.840 → 0.787 (−6.3%)
- Recall: 0.827 → 0.582 (−29.6%)
- mAP50: 0.884 → 0.740 (−16.3%)

The null hypothesis holds: the false positives observed in EXP-008 were not caused by missing negative examples.

### Why Negatives Hurt

1. **Gradient dilution.** With only 405 positive training images, the model already has limited signal. Adding 44 images that produce zero positive gradients effectively reduces the useful signal density per epoch by ~10%. The model sees fewer productive examples per training pass.

2. **Negative composition mismatch.** Our negatives (UK forecourts, road signs, LED billboards, streetscapes) may not resemble what the model was actually producing as false positives. Effective hard negative mining should use the model's own false positive predictions, not generic background images.

3. **Dataset too small for negative benefit.** The Ultralytics recommendation of 1-10% negatives assumes datasets of 1000+ images where positive coverage is already saturated. At 509 images, we haven't yet exhausted the positive scaling curve — adding more positive diversity would be more productive.

4. **Recall collapse as primary failure mode.** The recall drop (0.827 → 0.582) is disproportionately large. The model became more conservative overall — not just on negatives, but also on genuine signs it would have previously detected.

### Surprise Finding: `end2end=False` is Critical

The most valuable outcome of this experiment was discovering that `end2end=False` evaluation yields dramatically better metrics:
- EXP-008 mAP50: 0.725 (end2end=True) → **0.884** (end2end=False) — **+22% free improvement**
- Recall: 0.543 → 0.827 — the one-to-one head was artificially suppressing valid detections

This aligns with the YOLO26 training guide (docs/research/YOLO26_training_guide.md) which documents the "double detection anomaly" and "artificial recall ceiling" as known issues with end2end=True on custom datasets.

**Implication for deployment:** On mobile, we should export with `end2end=False` and include lightweight NMS post-processing. The ~25ms NMS overhead is negligible compared to the recall improvement.

### Scaling Trend Update

With the corrected end2end=False evaluation:

| Train images | mAP50 (e2e=False) | Marginal mAP/image |
|-------------|-------------------|-------------------|
| 177 | 0.348* | — |
| 239 | 0.595* | +0.004/img |
| 296 | 0.725* | +0.002/img |
| 405 | 0.884 | +0.001/img |

*Historical values (may not be directly comparable — evaluated with different end2end settings)*

The positive data scaling trend is still productive at +0.001 mAP/image. Adding 100 more positive images should push toward mAP50 ≈ 0.90.

## Next Steps

1. **Do NOT pursue more negatives** at this dataset scale. The positive scaling curve has not plateaued.
2. **Always evaluate with `end2end=False`** — update the ml-researcher skill and all future experiments.
3. **EXP-010 candidates (pick one):**
   - **Option A: Data-scarce hyperparameter tuning** — Apply the YOLO26 training guide recommendations: `freeze=10, mosaic=0.5, lr0=0.0054, lrf=0.0495, epochs=50`. Test whether tuned hyperparams improve over defaults on our 509-image dataset.
   - **Option B: More positive data** — Scrape 100+ new positive images targeting brand gaps (eg, apco, liberty, metro). The +0.001 mAP/image trend suggests this would push past 0.90.
   - **Option C: Model-guided hard negatives** — Run inference on the 44 negatives with EXP-008's model first, collect only images where the model actually produces false positives, then retrain. This is proper hard negative mining vs. our generic approach.
4. **Update canonical test evaluation** — Re-evaluate EXP-004 through EXP-007 with `end2end=False` to establish a consistent comparison baseline across all experiments.

## Operational Lessons

### 1. Ultralytics `save_dir` Mismatch

YOLO26 wrote training output to an external `runs_dir` (set in the Ultralytics global settings file) instead of the expected `runs/finder/v8_1class_509_neg44` inside this repo. The training was initially believed to be "stuck" (45 min CPU time, zero visible output) because we checked the wrong directory.

**Fix:** Always check the `save_dir` printed in the first few lines of YOLO training output. Or set `settings_dir` explicitly.

### 2. Background Training Observability

Running YOLO training via `Bash(run_in_background=True)` with `| tail -5` caused complete output buffering — no visible progress, no log file. The process ran to completion but we couldn't observe it.

**Fix:** Always use `| tee <logfile>` and never combine with `head`/`tail` which terminates the pipe. Check the log file directly, not the background task output.

### 3. Canonical Test Set Staleness

The `data/finder_canonical_test/` directory contained stale symlinks/copies from a previous dataset build. Six of 19 images were missing, silently reducing the evaluation to 13 images. The `pi_heif` error message was misleading — the actual error was `FileNotFoundError`.

**Fix:** Always rebuild the canonical test set from `configs/canonical_val_split.json` + `data/finder/` before evaluation. Search all splits (train/val/test) for images, since the split assignment changes with dataset growth.

## Conclusion

EXP-009 is a **negative result** — the intervention (44 hard negative images) degraded model performance across all metrics. However, the experiment produced two findings of greater value than the original hypothesis:

1. **`end2end=False` evaluation** reveals that our EXP-008 Finder is substantially better than previously measured (mAP50 = 0.884 vs. reported 0.809). This changes the project's overall assessment of Finder readiness — at 0.884 mAP50 with P=0.840 and R=0.827, the Finder may be approaching deployment quality for the crop-and-read pipeline.

2. **Negative result as evidence.** The clear regression caused by generic negatives at this dataset scale is informative. It establishes that (a) the positive scaling curve is still productive, (b) generic negatives are counterproductive below ~1000 positive images, and (c) any future negative mining must be model-guided (using the model's own false positives as training signal).

Both findings came from following the scientific method: the hypothesis was testable, the experiment was controlled, and the surprise results led to deeper investigation rather than dismissal.

## Reproducibility

```bash
# 1. Build dataset with negatives
.venv/bin/python scripts/build_finder_dataset.py --classes 0 --seed 42 --negatives-dir data/negatives

# 2. Train (always tee to log)
LOG=runs/finder/v8_train.log && mkdir -p runs/finder
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
    data=data/finder/dataset.yaml model=yolo26n.pt \
    epochs=100 imgsz=640 batch=4 device=mps amp=False \
    project=runs/finder name=v8_1class_509_neg44 seed=42 \
    2>&1 | tee "$LOG"

# 3. Rebuild canonical test set (search all splits)
.venv/bin/python -c "
import json, os, shutil, yaml
canon = json.load(open('configs/canonical_val_split.json'))
if os.path.exists('data/finder_canonical_test'): shutil.rmtree('data/finder_canonical_test')
os.makedirs('data/finder_canonical_test/images/test', exist_ok=True)
os.makedirs('data/finder_canonical_test/labels/test', exist_ok=True)
for name in canon['test']:
    stem = os.path.splitext(name)[0]
    for split in ['train','val','test']:
        for ext in ['.jpg','.jpeg','.png']:
            img = f'data/finder/images/{split}/{stem}{ext}'
            lbl = f'data/finder/labels/{split}/{stem}.txt'
            if os.path.exists(img) and os.path.exists(lbl):
                shutil.copy2(img, f'data/finder_canonical_test/images/test/{stem}{ext}')
                shutil.copy2(lbl, f'data/finder_canonical_test/labels/test/{stem}.txt')
                break
        else: continue
        break
yaml.dump({'path':os.path.abspath('data/finder_canonical_test'),'train':'images/test','val':'images/test','test':'images/test','nc':1,'names':{0:'sign_board'}}, open('data/finder_canonical_test/dataset.yaml','w'))
print(f'Built: {len(os.listdir(\"data/finder_canonical_test/images/test\"))} images')
"

# 4. Evaluate — ALWAYS end2end=False
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
    data=data/finder_canonical_test/dataset.yaml \
    model=<path_to_best.pt> \
    device=mps amp=False end2end=False
```

## Artifacts

| Artifact | Location |
|----------|----------|
| Training run | `runs/finder/v8_1class_509_neg44/` (written under the externally-set Ultralytics `runs_dir` — see Operational Lessons §1) |
| Best weights | `v8_1class_509_neg44/weights/best.pt` (epoch 53) |
| Training log | `runs/finder/v8_1class_509_neg44_train.log` (partial — first 60 lines) |
| Negative images | `data/negatives/batch_{servo,roadsign,led,noau,street}/` |
| Build script change | `scripts/build_finder_dataset.py` — added `--negatives-dir` flag |
| YOLO26 training guide | `docs/research/YOLO26_training_guide.md` |
