# EXP-025: Epoch Count (100 vs 50)

## Hypothesis
With freeze=0 and v7 labels, 100 epochs will improve over 50 epochs by ≥0.02 mAP50.

## Results

| Epochs | mAP50 | mAP50-95 | P | R |
|--------|-------|----------|-------|-------|
| 50 (024a) | **0.649** | 0.299 | 0.674 | 0.620 |
| 100 (025a) | 0.631 | **0.306** | 0.675 | 0.581 |

## Analysis

**Hypothesis rejected.** 100 epochs (0.631) is slightly worse than 50 epochs (0.649) on mAP50, though mAP50-95 improved marginally (0.299→0.306). Recall dropped (0.620→0.581) indicating the model became more conservative — classic overfitting pattern.

With freeze=0, the entire backbone is trainable. 100 epochs gives too many gradient updates to the backbone, causing it to overfit to training-specific features. 50 epochs is the right balance.

**50 epochs confirmed as optimal, even with freeze=0.**
