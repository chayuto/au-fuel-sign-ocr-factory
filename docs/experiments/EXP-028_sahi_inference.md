# EXP-028: SAHI Sliced Inference (Zero Training)

## Hypothesis
SAHI with 320×320 slices will detect more signs than standard 640×640 inference, especially distant/small signs.

## Results (Quick Test — 10 images)

| Method | Detected | Miss |
|--------|----------|------|
| Standard (640×640) | 5/10 | 5 |
| **SAHI (320×320 slices)** | **8/10** | **2** |

**+60% more detections with zero retraining.**

## Analysis

SAHI works by slicing the image into overlapping patches. Small signs that are 20-50px in a 640px image become 40-100px in a 320px patch — much easier for YOLO to detect.

This is directly relevant to the dashcam scenario: distant signs at 50-100m are small in the frame. SAHI makes them detectable during the "approach phase" before the sign is close enough for standard inference.

**Caveat:** This is a detection count test, not a full mAP evaluation. The SAHI detections need to be validated against ground truth boxes for proper mAP scoring. Also, SAHI runs ~10× slower (multiple patches per image) so it's a quality/speed tradeoff.

## Real-World Application

```
Dashcam pipeline:
  - Sign at 100m → SAHI inference (slow but catches distant signs)
  - Sign at 30m → Standard inference (fast, sign is now large)
  - Sign at peak size → Crop + read prices
```

## Next Steps
- Full mAP evaluation with SAHI on all 50 test images
- Test different slice sizes (480×480 for speed vs 320×320 for accuracy)
- Measure inference latency per image with SAHI
