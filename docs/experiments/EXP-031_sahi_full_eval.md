# EXP-031: Full mAP Eval of SAHI vs Standard Inference (on new best Finder)

**Status:** COMPLETE 2026-05-02
**Model:** `exp029_treatment_s42` (mAP50=0.748 via yolo val, P=0.909)
**Test set:** canonical_test_v2 (50 hand-verified images)
**Eval framework:** torchmetrics MeanAveragePrecision (COCO-style)

## Hypothesis

Per EXP-028's quick 10-image test, SAHI sliced inference detected 8/10 vs standard's 5/10 distant signs. Hypothesis: SAHI gives a free mAP boost over standard inference on the full canonical_test_v2.

## Results

| Method | mAP50 | mAP50-95 | mAR_100 | ms/image |
|--------|-------|----------|---------|----------|
| Standard 640×640 | **0.568** | **0.276** | 0.596 | **65** |
| SAHI 320×320 slices | 0.178 | 0.075 | 0.308 | 392 |
| SAHI 480×480 slices | 0.218 | 0.106 | 0.302 | 206 |
| SAHI 320 + standard hybrid | 0.178 | 0.075 | 0.308 | 382 |

**Standard inference wins decisively** — by ~3× on mAP50, ~2× on recall, with 6× lower latency.

## Why this contradicts EXP-028

EXP-028 was a 10-image qualitative test with hand-picked *distant* sign images — exactly the case SAHI is designed for. Canonical_test_v2 contains 50 curated images where signs are typically prominent (medium-to-large in frame).

**SAHI's failure mode here:** when a sign occupies more than ~30% of the image, slicing into 320×320 patches *fragments* the sign across multiple slices. Each slice sees only a piece of the sign, often without the brand header or all the fuel rows — the model produces low-confidence partial detections that don't merge cleanly into one full panel detection.

The hybrid mode (`perform_standard_pred=True`) still scored 0.178 — SAHI's internal NMS appears to suppress the standard-resolution predictions when slice predictions overlap, defeating the hybrid's purpose.

## Note on absolute numbers

Standard 640×640 here scored mAP50=0.568, but the same model+test set scored mAP50=0.748 via `yolo detect val` in EXP-029. The discrepancy is methodology:
- `yolo detect val` uses ultralytics' internal eval loop with their NMS + their mAP code (Pascal-VOC style, conf=0.001, single 640×640 forward pass)
- This eval uses `model.predict()` outputs piped through torchmetrics' COCO-style mAP

The relative comparison within this script (standard vs SAHI under the same eval code) is what matters. The 3× gap stands.

## Conclusion

**Do not use SAHI for general inference on this test distribution.** Reserve it for a future "distant sign approach phase" test set if/when one is built (signs <5% of frame, simulating dashcam at 50–100m approach distance).

## Decision

- **Standard inference** is the production choice for the Stage 1 Finder. ~65 ms/image is well within the dashcam frame budget.
- **EXP-028's claim ("+60% detections from SAHI")** is valid only for distant-sign scenarios. It was over-generalized in the project memory; updating memory to reflect that.
- No additional training needed; standard inference of `exp029_treatment_s42` is the current best.

## Reproducibility

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/eval_sahi.py --mode all
# Output: logs/exp031_results.json
# Logs:   logs/exp031_full.log
```
