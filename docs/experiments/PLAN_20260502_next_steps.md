# Forward Plan — drafted 2026-05-02

After: data cleanup pass + EXP-029/030/031. State: 630 annotations, best Finder mAP50=0.692 clean, not yet republished.

## What's gating progress

The pipeline goal is a working dashcam fuel-sign reader. The gating questions are:

1. **Does the Finder actually work in the field?** (mAP on a curated 50-image test ≠ "works in real dashcam footage")
2. **Is the Finder good enough to feed Stage 2?** (the project doc set the gate at mAP50 > 0.70 — we're at 0.692 clean, essentially at the gate)
3. **Can we ship the model on-device?** (no TFLite export ever attempted — could fail at the boundary)
4. **Will more data help?** (123 v7_auto remain to clean; gap brands are scarce on web; Stage 2 work could pull on different data than Stage 1)

## Recommended next moves, in priority order

### Tier 1 — high value, low cost (do these first when you resume)

**1. Real-footage qualitative test** (~1 hr, IF dashcam video exists)
Run `exp030_clean_s43/weights/best.pt` against any real driving footage. Watch for:
- Detection consistency across frames as the car approaches a sign
- False positives on shop/street signage that isn't fuel
- Performance at distance vs close-up
- Brands the model has seen vs hasn't

This is the *actual product question* and we've never answered it. mAP50 is a proxy.

**2. TFLite export smoke test** (~2 hrs)
Goal: prove the model can be deployed on-device. Steps:
- `yolo export model=exp030_clean_s43/weights/best.pt format=tflite int8=True`
- Verify the exported model runs on a simulator or python tflite-runtime with reasonable latency
- Compare detection outputs vs the .pt model on a few canonical images
- Document any operator coverage gaps (YOLO26 may have ops that don't quantize cleanly)

If TFLite export fails or numbers degrade significantly, that's a real product blocker we want to know about now, not after Stage 2 is built.

### Tier 2 — high value, medium cost

**3. Test set expansion to 100–150 images** (~2–3 hrs of labeling)
The 50-image test gives ±0.014 single-seed CI. Expanding to 150 cuts variance ~30%, enabling detection of smaller A/B effects. Source: pull from `data/tmp/` images that aren't in train/val and weren't ever labeled, hand-verify v7. Stratify across brands.

This is the prerequisite for *any* future A/B that wants to claim significance for small effects.

**4. Stage 2 prototype kickoff** (open-ended)
Finder is at P=0.744 on clean test — high precision is exactly what Stage 2 wants (clean panel crop, fewer false-positive crops to filter). The architecture is documented in CLAUDE.md:

```
Stage 2:
  → Crop sign panel from original-resolution frame using Finder bbox
  → Brand classifier on top region (15-class CNN, ~1MB)
  → Row detector via classical CV (horizontal projection + peak detection — no ML)
  → For each row:
      → Right half → Price reader (CRNN+CTC, ~1.5MB)
      → Left half  → Fuel type classifier (8-class CNN, ~0.5MB)
  → Validation (price 80–350 cents, fuel type closed enum)
```

Suggested first step: **classical CV row detector**. No training needed; just OpenCV horizontal projection on the cropped panels. Validate against the 50-image test set's v7 annotations (if entries are populated) or a quick hand-validation. This is the cheapest piece to prototype and de-risks the whole Stage 2 design.

### Tier 3 — productive but not urgent

**5. Resume v7_auto QA loop** (123 stems left, ~2.5 hrs of agent time) — **BLOCKED on prompt fix below**
The labels are demonstrably wrong by visual inspection (~80% had bbox errors). EXP-030 didn't show a metric improvement, but cleaner labels are still cleaner labels. Worth completing if/when relabel cycles are available. Resume command:
```python
# Pick next 5 v7_auto stems (alphabetical, deterministic)
import json, os
ann = 'data/tmp/annotations'
remaining = sorted([fn[:-5] for fn in os.listdir(ann)
    if fn.endswith('.json') and json.load(open(f'{ann}/{fn}')).get('prompt_version') == 'v7_auto'])
batch = remaining[:5]
```
Prompt template: `qa_seq` style from yesterday (per-stem commit, neutral framing).

**5a. Prerequisite — fix the v7 prompt's co-brand edge case** (~30 min, BLOCKER)
Audit on 2026-05-02 of 8 random QA decisions found a 25% systematic error: agents excluded the **Shell pecten** at the top of Shell+Coles co-branded pylons, classifying it as a "separate brand header" rather than "the brand logo at top." Same gap likely affects BP+Wild Bean, Caltex+Woolworths, Ampol+Foodary. See `feedback_qa_agent_shell_coles_bug.md`.

What to do before any more QA:
1. Add a worked-examples section to `.claude/skills/fuel-sign-labeler/SKILL.md` (and the QA prompt template) showing Shell+Coles, BP+Wild Bean, Caltex+Woolworths cases with the pecten/brand-mark INCLUDED.
2. State the rule explicitly: *"If a brand mark is mounted on the same pylon structure as the price panel — even above a co-brand band — INCLUDE it."*
3. Targeted re-pass on existing v7_qa: filter `*coles*` and `*shell*coles*` filenames, re-audit Shell pecten specifically (~20–40 stems max).

Don't run more QA agents on the remaining 123 v7_auto until this lands — would just compound the same error.

**5b. Optional — grid overlay for bbox precision** (~1 hr to test, separate from 5a)
Hypothesis: rendering a 10×10 normalized grid (0.0/0.1/0.2... axis labels) on the labeling preview anchors the agent's coordinate output to discrete reference points and reduces drift. Known VLM technique; would help with loose-bbox errors specifically (would NOT have caught the Shell-pecten rule miss — that's 5a's job).

Cheapest test: render gridded preview as a separate image, run 10 stems through the labeler with both gridded and ungridded variants, IoU-compare bboxes against a hand-drawn ground truth. If gridded IoU is materially higher (say >0.03), integrate into the labeling skill. Tradeoff to watch: agents may snap to gridlines instead of true panel edges. 20×20 reduces snap error but adds clutter.

Sequence: do 5a first (rule fix is the bigger lever); 5b is a second-order precision improvement on top of correct rules.

**6. Build "distant signs" eval set, re-test SAHI**
EXP-031 showed SAHI hurts on prominent-sign images. The original SAHI claim ("+60% detections on distant signs") may still be valid for the dashcam approach phase. To confirm: collect ~20 hand-labeled images of signs at 50–100m approach distance, eval SAHI vs standard on that set specifically. If SAHI wins on distant test, build a hybrid inference pipeline (standard + SAHI fallback when standard finds nothing).

### Tier 4 — wait until necessary

**7. HuggingFace republish**
Hold until one of: (a) a model genuinely beats 0.692 clean mAP50, (b) significantly larger test set giving credible publication numbers, (c) Stage 2 working end-to-end so we ship the full pipeline together. See `project_publish_hold_20260502.md`.

**8. Scrape gap brands again**
Bing pool for OTR/EG/Liberty/Costco is 95% exhausted (today's run). Don't bother with more Bing scraping. Alternatives if dataset growth is needed:
- News articles via Bing news search
- Flickr photographers (already partly mined)
- Facebook public station pages (manual)
- Manual collection from your own driving (high quality but slow)

## What would I do first when resuming?

In order, assuming any of these are blocked I move to the next:

1. **Real-footage qualitative test** — answers "does it actually work" (1 hr)
2. **TFLite export smoke** — de-risks the deployment boundary (2 hrs)
3. **Classical CV row detector prototype** — cheapest Stage 2 piece, no training needed (3 hrs)

After those three, we have a much better understanding of what to invest in next: more data, model improvements, or polish for shipping.

## Decision log to revisit

- **Test set expansion is the single biggest CI tightener.** When you next plan an A/B for a small effect (~+0.02 mAP50), expand test set FIRST.
- **Don't run more Bing scrape on gap brands.** 95% dedup rate confirms the well is dry.
- **Don't re-run SAHI on canonical_test_v2.** It's the wrong tool for that distribution. Build a distant-sign set if you want to revisit.
- **Don't republish HF until model genuinely improves.** Lower-but-cleaner numbers look like a regression to the public.

## Open questions to answer next session

1. Does `exp030_clean_s43` work on real dashcam footage? (qualitative test)
2. Does it survive TFLite INT8 quantization? (export test)
3. Does classical CV row detection on the 50-test crops align with v7 annotations? (Stage 2 viability)
4. Is the 123 v7_auto cleanup worth completing for future training, even if it didn't move EXP-030 metrics?
