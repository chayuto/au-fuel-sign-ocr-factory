# Scrape Report: v4 Slot 4 — YouTube Thumbnails (Costco & OTR)

## Summary
- **Images saved:** 20
- **Images rejected:** 0
- **Brands covered:** costco, otr
- **Hit rate by source:** YouTube thumbnails → 20 saved / 20 attempted (100%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| YouTube query: `Costco fuel Australia 2025` | success | 4 | Extracted candidate video IDs and downloaded valid thumbnails |
| YouTube query: `Costco petrol price Australia` | success | 2 | Added unique Costco IDs |
| YouTube query: `cheapest fuel Australia Costco` | success | 2 | Added additional Costco IDs |
| YouTube query: `Costco fuel queue Australia` | success | 2 | Added additional Costco IDs |
| YouTube query: `OTR fuel prices Adelaide` | success | 5 | Extracted OTR-focused Adelaide IDs |
| YouTube query: `On The Run fuel price Adelaide` | success | 5 | Added additional OTR IDs |

## What Worked
- Direct thumbnail endpoint pattern worked reliably: `https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg`.
- Fallback to `hqdefault.jpg` was available when needed.
- Verification checks (MIME type and size >5KB) filtered out invalid placeholders/errors.
- Gap-brand targeting was effective: batch is fully focused on Costco and OTR.

## What Didn't Work
- Initial TSV parsing attempt in shell script concatenated fields unexpectedly and produced invalid verification outcomes; replaced with Python-based downloader for robust parsing.
- Fully automatic quality filtering for "usable sign visible" still requires downstream visual QA during labeling.

## Suggestions for v5
- Expand Slot 4 with newer year-bounded searches (`2026`) and city-specific variants (`Costco Docklands`, `OTR Adelaide`).
- Add an OCR pre-screen to prioritize thumbnails containing clear numeric price text before manual labeling.
- Combine Slot 4 with targeted News slot queries for Costco/OTR to diversify beyond thumbnails.
