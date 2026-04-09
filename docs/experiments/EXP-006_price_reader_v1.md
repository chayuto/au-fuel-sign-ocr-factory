# EXP-006: Price Reader — First Training Attempts

## Hypothesis

968 real price crops with 12-token CTC vocabulary is sufficient to train a working price reader.

## Setup

### Data
- 942 real price crops extracted from 303 annotated images (6 missing images, 4 bad prices)
- 801 train / 141 val (seed=42, 15% val)
- 277 unique prices, range 47.1–306.9
- Crop dimensions: 48px height, 15–249px width (mean 111)
- Fuel types: U91, E10, P95, P98, Diesel, LPG

### Models Tried

| Run | Architecture | Params | Train data | Result |
|-----|-------------|--------|-----------|--------|
| v1 | SimpleCRNN | 764K | 801 real | **Failed** — char_acc stuck at 20%, field_acc=0% |
| v2 | SimpleCRNNTiny | 66K | 801 real | **Failed** — identical collapse |
| **v3** | **SimpleCRNNTiny** | **66K** | **10K synth + 801 real** | **Partial** — char_acc=47%, field_acc=5.7% |

## Analysis

### v1/v2: CTC Mode Collapse
Both models collapsed to predicting "1.9" for all inputs. Loss plateaued at ~1.4. This is a classic CTC failure: with only 801 samples, the model cannot learn feature extraction AND CTC alignment simultaneously. Model size (66K vs 764K) made no difference — the bottleneck was data volume, not capacity.

### v3: Synthetic Pretraining Breaks Collapse
Adding 10K synthetic price images (cv2.putText on varied backgrounds) broke through the collapse:
- Train loss dropped to 0.11 (synth is easy to learn)
- Val char_acc reached 47% (up from 20% baseline)
- Val field_acc reached 5.7% (1 correct prediction in 20)
- Model predicts real-looking prices ("149.9", "139.9") instead of constant "1.9"

### Domain Gap is the Blocker
Predictions on real crops show the model learned digit recognition but struggles with:
- LED segment vs rendered font appearance
- Background texture differences (dark sign panels vs uniform cv2 backgrounds)
- Digit spacing and proportions differ from cv2.putText

Example predictions:
```
gt="122.9" pred="129.9"  — close, confused 2→9
gt="163.9" pred="19.9"   — lost middle digits
gt="149.9" pred="149.9"  ✓ exact match
gt="215.9" pred="149.9"  — defaulting to common pattern
```

## Key Findings

1. **CTC requires >1000 samples minimum** — 801 real crops is insufficient regardless of model size
2. **Synthetic pretraining works** — breaks CTC collapse, proves the architecture is viable
3. **Domain gap is now the bottleneck** — cv2.putText fonts don't look like LED displays
4. **The model is learning** — predictions are plausible prices, not random

## Subsequent Runs: LED Synth + Two-Stage Training

| Run | Architecture | Train data | char_acc | field_acc | Notes |
|-----|-------------|-----------|----------|-----------|-------|
| v4 stage1 | CRNNTiny | 50K LED synth + 801 real | 23% | 0% | LED synth worse than font synth |
| v4 stage2 | CRNNTiny (ft) | 801 real (from stage1) | 26% | 0% | Fine-tune didn't recover |
| v5 | SimpleCRNN | 50K LED synth + 801 real | 20% | 0% | Bigger model no help |
| v6 | CRNNTiny (ft v3) | 801 real (from v3) | 50% | 4.3% | Fine-tune v3, no improvement |

**LED synth was worse than font synth** — too uniform (all dark bg + bright segments). The font-style synth in v3 provided more visual diversity that helped CTC.

**CTC is fundamentally limited at 801 samples.** Error analysis of v3:
- 29% wrong length (CTC alignment failure)
- 53% multi-digit errors
- Only 13% off-by-1 (close calls)

## Breakthrough: PriceClassifier (Fixed-Position Classification)

**Key insight:** Prices are always XX.X or XXX.X format → 4 independent classification heads (0-9 + blank). No CTC alignment needed.

| Run | Architecture | Data | char_acc | field_acc | Best |
|-----|-------------|------|----------|-----------|------|
| **cls_v1** | **PriceClassifier** | **801 real only** | **53%** | **9.2%** | **Yes** |

Per-head accuracy (cls_v1, epoch 92):
- Hundreds digit: 70% (limited range, easy)
- Tens digit: 25% (hardest — most visual ambiguity)
- Ones digit: 30%
- Tenths digit: 87% (mostly .9, easy)

**9.2% field accuracy with real data only** — better than all CTC attempts including synth-augmented.

## Next Steps (ranked by ROI)

1. **Add synth to classifier** — PriceClassifier + 50K LED synth (training now)
2. **More real crops** — label 36 pending images → ~1050 real crops
3. **Improve crop quality** — tighter bboxes, filter low-resolution crops

## Reproducibility

```bash
# Extract crops
.venv/bin/python scripts/extract_price_crops.py --seed 42

# Generate synth
.venv/bin/python scripts/generate_synth_prices.py --count 10000 --output data/reader_experts/price/synth

# Train (v3 — synth + real, tiny model)
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -u scripts/train_reader.py \
    --expert price --data data/reader_experts/price \
    --synth data/reader_experts/price/synth \
    --output runs/reader/price_v3_synth --epochs 80 --batch-size 64 --lr 0.001 --tiny
```
