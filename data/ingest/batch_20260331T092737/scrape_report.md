# Scrape Report: v4 Slot 1 — Wikimedia Gap Brands

## Summary
- **Images saved:** 3
- **Images rejected:** 45 (non-image files, 403/download failures, dedup skips, or out-of-scope)
- **Brands covered:** liberty, otr, puma
- **Hit rate by source:**
  - Wikimedia API search/category pass → 3 saved / 48 attempted (6.3%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `Category:On_The_Run_(convenience_stores)` | success | 1 | OTR Alphington image downloaded and validated |
| `Category:Puma_Energy` | success | 1 | Puma Truganina image downloaded and validated |
| `search: "Liberty fuel" OR "Liberty Oil"` | success | 1 | Liberty Oil Werribee image downloaded and validated |
| `Category:7-Eleven_in_Australia` + related search queries | failed | 0 | results mostly unavailable (403) or no usable fuel-price-board shots |
| `Category:Costco_Australia` + related search queries | failed | 0 | no relevant station price-board files returned |
| `search: "Metro Petroleum"` + related search queries | failed | 0 | no relevant station price-board files returned |

## What Worked
- Wikimedia `action=query` + `prop=imageinfo` was reliable for pulling direct media URLs.
- Category members for OTR/Puma surfaced modern Australian station photos.
- Validation checks (`size > 5KB` and `file` MIME confirmation) filtered bad responses effectively.

## What Didn't Work
- Brand-name searches for Costco/Metro returned mostly unrelated PDFs or non-station content.
- Several candidate image pages returned `403` when attempting direct download.
- Dedup guardrails reduced available near-duplicate pulls from the same station sequence.

## Suggestions for v5
- Expand Slot 1 with deeper pagination on `Category:On_The_Run_(convenience_stores)` and `Category:Puma_Energy` to find more distinct stations.
- Pair Wikimedia search with manual curation from article pages before file download to avoid PDF-heavy query noise.
- For Costco/Metro gap fill, prioritize non-Wikimedia high-yield sources (Slot 4/6) since Wikimedia coverage appears sparse.

## Saved Files
| Brand | File | Size (KB) | Notes |
|-------|------|-----------|-------|
| liberty | `wiki_liberty_australia_liberty_oil_werribee_nov.jpg` | 586.6 | Liberty Oil Werribee (AU) |
| otr | `wiki_otr_alphington_vic_otr_alphington_april_202.jpg` | 2674.7 | OTR Alphington VIC (AU) |
| puma | `wiki_puma_melbourne_vic_puma_truganina_november_.jpg` | 641.4 | Puma Truganina VIC (AU) |
