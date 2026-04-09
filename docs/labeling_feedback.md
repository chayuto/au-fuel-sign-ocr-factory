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

### Session: sonnet_v5 batches A–G (2026-04-08, caltex2/eg/puma/liberty/metro/mobil2)

**Overall: 8 labeled / 27 skipped (23% yield) across 7 batches of 5**

| Batch | Source | Labeled | Skipped | Yield | Root cause |
|-------|--------|---------|---------|-------|------------|
| A | caltex2 | 2 | 3 | 40% | Editorial/facade shots, brand-only crops |
| B | caltex2 | 3 | 2 | 60% | Good — LED sign photography |
| C | eg | 1 | 4 | 20% | Placeholder zeros, too-distant shots, pump close-ups |
| D | puma | 0 | 5 | 0% | **Brand press/marketing photography, non-AU locations** |
| E | liberty | 0 | 5 | 0% | **US Liberty Oil stations mixed in (same branding)** |
| F | metro | 0 | 5 | 0% | **Wrong results entirely: African stations, mall pylons, LED manufacturer** |
| G | mobil2 | 2 | 3 | 40% | Bloomberg editorial, US station, canopy-only shot |

**Source-level findings:**
- **caltex2** — viable at 40–60%. Skip pattern: brand logo crops, "save 4c" promo shots without price rows.
- **mobil2** — viable at 40%. Skip pattern: US Mobil stations, Bloomberg editorial watermarks. Usable images are 7-Eleven/Mobil co-branded pylons.
- **eg** — low yield (20%). EG Group uses wide architectural shots and placeholder-price launch photography.
- **puma** — **RETIRE.** 0% yield. All brand marketing: tropical non-AU locations, pre-opening stations, press-release composites.
- **liberty** — **RETIRE until query fixed.** US "Liberty Oil" looks identical to Australian Liberty. Must add "Australia" to filter.
- **metro** — **RETIRE until query fixed.** "Metro" too generic — returns Metro supermarkets, TOTAL Metro (Africa), mall pylon signs. Use "Metro Petroleum Australia price sign".

**Action items:**
- [ ] Bulk-mark all remaining `puma` pending rows as skipped
- [ ] Bulk-mark all remaining `metro` pending rows as skipped
- [ ] Re-scrape `liberty` with query: `"Liberty Oil Australia fuel price sign"`
- [ ] Re-scrape `metro` with query: `"Metro Petroleum Australia price sign"`
- [ ] For `caltex2`: add `-save -discount -"woolworths rewards"` to filter promo-only shots

---

### Session: sonnet_v5 batches H–Q (2026-04-09, coles/nsw/mobil2/tas/outrage2/ripoff/seven/vic/bp2/otr)

**Overall: 18 labeled / 50 processed (36% yield) across 10 batches of 5**

| Batch | Source | Labeled | Skipped | Yield | Root cause |
|-------|--------|---------|---------|-------|------------|
| H | coles | 2 | 3 | 40% | Distant shots, iStock watermark, logo-only crop |
| I | nsw | 2 | 3 | 40% | Night shot with no sign, "no fuel" sandwich board, highway road sign |
| J | mobil2 | 2 | 3 | 40% | PR handshake photo, US 7-Eleven, canopy-only shot |
| K | tas | 2 | 3 | 40% | Manufacturer LED render (888), UK BP sign, UK Shell sign |
| L | coles | 2 | 3 | 40% | Too small/distant signs |
| M | outrage2 | 0 | 5 | 0% | **All price charts/infographics** — 6 remaining bulk-skipped |
| N | ripoff | 1 | 4 | 20% | Pump nozzle shot, US sign, infographic composite, man+jerry cans |
| O | seven | 1 | 4 | 20% | Promo pylon (no prices), store exterior, US 7-Eleven, pump nozzles |
| **P** | **vic** | **5** | **0** | **100%** | **All labeled — night shots, BP, Caltex, Shell pylons** |
| Q | bp2+otr | 1 | 4 | 20% | bp2: vintage pump, South Africa BP, logo-only, forecourt glamour shot |

**Dataset after session: 332 done, 1031 skipped, 434 pending**

**Source-level findings:**
- **vic** (Victoria state-specific) — **100% yield.** Best source found. All 5 images were clear AU pylon signs across multiple brands (BP, Caltex/EG, Shell).
- **coles / nsw / mobil2 / tas** — consistent 40%, matching prior sessions.
- **outrage2** — **RETIRE.** 0% yield. All price comparison charts and line graphs. Same pattern as "cheap" query. Bulk-skipped all remaining.
- **ripoff / seven** — 20% yield. Mostly wrong content (pump shots, US stations, store interiors).
- **bp2** — 0% in this batch. Non-AU stations (South Africa), vintage pump, glamour architecture shots.

**Action items:**
- [ ] Prioritise `vic`-style state+brand queries for future scrapes (e.g., "BP fuel price sign Victoria", "Shell petrol price VIC")
- [ ] Bulk-skip remaining `ripoff` and `seven` if yield stays ≤20%
- [ ] Re-scrape `bp2` with query: `"BP Australia fuel price sign"` + state suffix

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
