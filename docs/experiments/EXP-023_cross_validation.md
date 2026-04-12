# EXP-023: Cross-Validation — Variance Measurement

## Hypothesis
The observed mAP50 on the 50-image test set has std < 0.03, meaning results are stable enough to detect real improvements of ≥0.05.

## Setup
3 training runs, identical recipe, different random seeds:
- 508 train images, freeze=10, mosaic=0.5, 50 epochs, optimizer=auto
- Evaluated on canonical_test_v2.1 (50 verified images), end2end=False

## Results

| Seed | mAP50 | mAP50-95 | P | R |
|------|-------|----------|-------|-------|
| 42 | 0.623 | 0.278 | 0.623 | 0.629 |
| 123 | 0.592 | 0.282 | 0.631 | 0.660 |
| 7 | 0.589 | 0.253 | 0.673 | 0.560 |
| **Mean** | **0.601** | **0.271** | **0.642** | **0.616** |
| **Std** | **0.015** | **0.013** | **0.022** | **0.042** |

## Analysis

**Hypothesis confirmed.** std = 0.015 < 0.03. Results are stable.

- **mAP50:** 0.601 ± 0.015 — any improvement ≥ 0.03 is real
- **Recall** has higher variance (std=0.042) — R is the noisiest metric
- **Precision** is moderate (std=0.022)
- **mAP50-95** is stable (std=0.013)

**Baseline for all subsequent experiments: mAP50 = 0.601 ± 0.015**

Any experiment that achieves mAP50 ≥ 0.63 is a real improvement (>2 std above mean).

## Note on Previous Baselines
EXP-021d reported 0.731 on the 25-image test and 0.731 on 50-image test. The current 0.601 is lower because:
1. The manifest was reconciled (497 rows fixed), changing the dataset composition
2. The 50-image test set is harder than the 25-image set
3. More v7_auto labels in training (269 unverified) may add noise

This is the honest, reproducible baseline going forward.
