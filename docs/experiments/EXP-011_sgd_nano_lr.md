# EXP-011: Explicit SGD with YOLO26 Nano LR Schedule

## Hypothesis

EXP-010-B used `optimizer=auto` which selected AdamW(lr=0.002) and silently ignored the specified lr0=0.0054/lrf=0.0495. By explicitly using `optimizer=SGD`, the YOLO26 nano-specific learning rate schedule (high initial lr=0.0054, aggressive decay lrf=0.0495) will be respected and may further improve on 10-B's mAP50=0.911.

**Expected:** mAP50 ≥ 0.91 (matching or exceeding 10-B)

## Setup

| Parameter | Value | vs 10-B |
|-----------|-------|---------|
| **optimizer** | **SGD(lr=0.0054, momentum=0.937)** | AdamW(lr=0.002) |
| **lr0** | **0.0054** (respected) | 0.0054 (ignored) |
| **lrf** | **0.0495** (respected) | 0.0495 (ignored) |
| freeze | 10 | same |
| mosaic | 0.5 | same |
| epochs | 50 | same |
| Dataset | 509 (405 train), no negatives | same |
| imgsz=640, batch=4, device=mps, amp=False, seed=42 | | same |
| Run | `v10_1class_509_sgd` | |

Confirmed in log: `SGD(lr=0.0054, momentum=0.937)` — lr schedule was actually applied.

## Results

### Canonical Test Set (19 images, end2end=False)

| Model | Optimizer | lr0 | P | R | mAP50 | mAP50-95 |
|-------|-----------|-----|-------|-------|-------|----------|
| EXP-008 (baseline) | AdamW(0.002) | — | 0.840 | 0.827 | 0.884 | 0.444 |
| 10-B (best) | AdamW(0.002) | — | 1.000 | 0.833 | **0.911** | **0.460** |
| **EXP-011** | **SGD(0.0054)** | **0.0054** | **0.822** | **0.727** | **0.784** | **0.394** |

### Best val epoch: 50 (P=0.512, R=0.474, mAP50=0.426)

Training time: ~25 min (50 epochs).

## Analysis

### Hypothesis Rejected

SGD with the nano lr schedule **underperformed** AdamW by a wide margin:
- mAP50: 0.911 → 0.784 (−14%)
- Recall: 0.833 → 0.727 (−12.8%)
- mAP50-95: 0.460 → 0.394 (−14.3%)

### Why SGD Underperformed

1. **AdamW is better for small datasets.** SGD's strength is generalization on large datasets where it avoids overfitting to noise. With only 405 images, the adaptive per-parameter learning rates of AdamW help the model converge faster and more completely within limited epochs.

2. **The nano lr schedule was designed for COCO (300K+ images).** The lr0=0.0054 with aggressive lrf=0.0495 decay is calibrated for massive datasets with dense gradients. On 405 images, the learning rate decays too quickly before the model has extracted sufficient signal.

3. **SGD + frozen backbone = double constraint.** With freeze=10, only the neck/head have trainable parameters. SGD's uniform update rule gives these parameters less adaptation ability than AdamW's per-parameter scaling.

### Key Takeaway

The YOLO26 training guide's nano lr schedule is optimized for COCO-scale training (100K+ images). For our data-scarce regime (509 images), **AdamW with auto lr is the correct choice**. The `optimizer=auto` selection was actually making the right call all along.

## Conclusion

**10-B remains the best model.** The winning recipe for 509 images:

```
freeze=10, mosaic=0.5, epochs=50, optimizer=auto (→ AdamW lr=0.002)
```

The SGD nano lr schedule is not beneficial at this dataset scale. Future optimizer experiments should only be revisited if the dataset grows past ~2000 images.
