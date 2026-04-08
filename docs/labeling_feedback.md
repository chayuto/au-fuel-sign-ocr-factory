# Labeling Agent Feedback Log

Collated feedback from labeling agents, organized by prompt version. Used to improve the labeling prompt over time.

## Prompt v5 (2026-04-08)

### Agent: opus_v5_01 (cheap batch 1)
- **Labeled:** 3/10 (30%)
- **Feedback:** High skip rate from "cheap" query — mostly charts/graphs/infographics. 70% of images were price comparison charts, not station photos.
- **Suggestion:** Exclude "cheap" query or add `-chart -graph -infographic` to search terms.

### Agent: opus_v5_02 (cheap batch 2)
- **Labeled:** 2/10 (20%)
- **Feedback:** Same issue — 80% charts. Alamy watermarked image had good sign but was unusable.
- **Suggestion:** Alamy watermarks shouldn't auto-reject — sign is still readable for detection training.

### Agent: opus_v5_03 (costco batch)
- **Labeled:** 2/10 (20%)
- **Feedback:** Most images are US/Canadian/UK Costco, not Australian. Costco signs use stacked vertical layout (label above price) which triggers Y-misalignment validator warnings — these are false positives for this sign type.
- **Suggestion:** Add "Australia" more prominently in Costco queries. Consider updating validator to handle stacked layouts.

### Agent: opus_v5_04 (NSW batch)
- **Labeled:** 4/10 (40%)
- **Feedback:** Better yield from state-specific queries. Skips were mostly: sign too small, no fuel sign in frame, closed/no-fuel signs. One labeled image had stacked LED layout triggering warnings.
- **Suggestion:** State-specific queries are the best strategy for volume.

### Agent: opus_v5_05 (VIC batch)
- **Labeled:** 5/10 (50%)
- **Feedback:** Best yield so far. 3 skips were stock watermarks (Getty/Alamy), 1 pump display, 1 watermark+too small. Label-above-price (stacked) layout triggers false validator warnings.
- **Suggestion:** Alamy watermarks should not auto-reject if sign is readable. Update validator for stacked layouts.

### Agent: opus_v5_06 (manifest-read) — pending

### Agent: opus_v5_qld (QLD batch)
- **Labeled:** 1/5 (20%)
- **Feedback:** 40% were Chinese manufacturer product photos (GUOSE brand, white background, placeholder 888.8 prices). 1 was Chinese Sinopec station. 1 was US composite. LPG price 53.9 below validator range of 60.
- **Suggestion:** Add negative search terms: -manufacturer -"LED display" -"signage company" -GUOSE -factory. Widen LPG range to 40-150. Include "Australia" or city names in all queries.

### Agent: opus_v5_wa1 (QLD+WA batch)
- **Labeled:** 1/5 (20%)
- **Feedback:** 2 stock watermarks (Alamy, AAPIMAGE) covering signs. 1 GUOSE manufacturer CGI. 1 FuelRadar logo (zero content). The one usable image was "Fresh Trading Co." independent truck stop — mapped to "independent".
- **Suggestion:** Add `-stock -alamy -shutterstock -aapimage` to scraper queries. Haiku screening should catch logos and CGI renders.
### Agent: opus_v5_wa2 (WA batch 2)
- **Labeled:** 2/5 (40%)
- **Feedback:** Alamy watermarks are dominant skip reason (2/3 skips). Low-res source images (612x454) make price reading uncertain — 1 image marked quality C. Caltex sign had printed/mechanical digits — sign_type taxonomy unclear.
- **Suggestion:** Filter Alamy at scrape stage. Add "close up" to queries to avoid distant shots. Consider adding "mechanical" or "flip" as sign_type option.

---

## Aggregated Insights (v5)

### Yield by query type
| Query type | Batches | Avg yield | Notes |
|-----------|---------|-----------|-------|
| "cheap fuel" | 2 | 25% | Mostly charts/infographics |
| Costco-specific | 1 | 20% | Mostly non-Australian Costco |
| State-specific (NSW) | 1 | 40% | Best yield so far |
| VIC/QLD/WA | pending | — | Expected similar to NSW |
| Alamy/Dreamstime | pending | — | Watermarked but potentially usable |

### Agent: opus_v5_col2 (Coles C)
- **Labeled:** 2/5 (40%)
- **Feedback:** All Shell/Coles Express from stock sites. 1 Alamy watermark, 1 iStock watermark, 1 logo-only crop. Both labeled images quality B (oblique angle, low res ~450px). LED digit ambiguity on diesel price.
- **Suggestion:** Stock photo sites are high noise. Brand diversity is low (all Shell/Coles same pylon design).

### Agent: opus_v5_sqld (suburb QLD)
- **Labeled:** 0/5 (0%)
- **Feedback:** Total wipeout. No fuel signs at all — hardware store, map, aerial photo, bar, motorsport. The query was too generic ("suburb qld").
- **Suggestion:** RETIRE generic suburb queries. Always include "fuel" OR "petrol" OR "servo" OR brand name. Brand+suburb is the winning formula (e.g., "BP petrol price sign Townsville").

### Common skip reasons (v5)
1. Charts/graphs/infographics (not photos)
2. Non-Australian stations (US/UK/EU)
3. Sign too small (<15% of frame)
4. No fuel sign in frame (canopy/exterior only)
5. Stock watermarks covering sign content
6. **Manufacturer product photos** (GUOSE, CGI renders) — NEW from v5 feedback
7. **Generic location queries returning non-fuel content** — NEW from v5 feedback

### Prompt improvement candidates
- [ ] Handle stacked sign layouts (label-above-price) in validator
- [ ] Clarify that stock watermarks are OK if sign is still readable
- [ ] Add negative search terms to scraper (`-chart -graph -infographic`)
- [ ] Costco queries need stronger "Australia" emphasis

---

## How to update this log

After each labeling agent completes, append its feedback here:
```markdown
### Agent: {agent_id} ({batch description})
- **Labeled:** X/Y (Z%)
- **Feedback:** {agent's challenges/observations}
- **Suggestion:** {agent's suggestions}
```

When incrementing prompt version, start a new section and summarize lessons from the previous version.
