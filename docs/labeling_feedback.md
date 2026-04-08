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

### Agent: opus_v5_05 (VIC batch) — pending
### Agent: opus_v5_06 (manifest-read) — pending
### Agent: opus_v5_qld (QLD batch) — pending
### Agent: opus_v5_wa1 (QLD+WA batch) — pending
### Agent: opus_v5_wa2 (WA batch) — pending

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

### Common skip reasons (v5)
1. Charts/graphs/infographics (not photos)
2. Non-Australian stations (US/UK/EU)
3. Sign too small (<15% of frame)
4. No fuel sign in frame (canopy/exterior only)
5. Stock watermarks covering sign content

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
