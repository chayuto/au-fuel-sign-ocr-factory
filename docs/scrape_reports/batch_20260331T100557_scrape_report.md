# Scrape Report: v4 Slot 8 — Automotive & Motoring Blogs

## Summary
- **Images saved:** 8
- **Images rejected:** 0
- **Brands covered:** independent (unbranded/mixed station signage)
- **Hit rate by source:**
  - drive.com.au → 8 saved / 8 attempted (100%)

## Sources Attempted

| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| https://www.drive.com.au/news/fuel-prices-today/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/news/motorists-caught-out-by-misleading-fuel-price-boards-nrma/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/news/nsw-service-station-price-board-laws-in-effect-now-backed-by-nrma/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/news/petrol-price-cap-plan-announced-by-victorian-government/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/news/cheap-petrol-will-soon-be-easier-to-find-due-to-victorian-fair-fuel-plan/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/caradvice/weekly-petrol-costs-australia-if-prices-increase-to-3-dollars-a-litre/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/caradvice/every-fuel-discount-in-australia-right-now/ | success | 1 | Hero image downloaded from `og:image` |
| https://www.drive.com.au/news/petrol-prices-will-increase-but-not-as-much-as-you-might-think/ | success | 1 | Hero image downloaded from `og:image` |

## What Worked
- Drive article pages consistently expose a direct `og:image` URL.
- Media URLs returned valid image binaries (all files > 5KB and identified as image/WebP by `file`).
- Required dedup checks (`data/ingest` + `data/tmp`) were executed per candidate keyword before downloading.

## What Didn't Work
- DuckDuckGo query results for other Slot 8 targets (`carsguide`, `whichcar`, `motoring`, `racv`, `nrma`) were sparse or noisy in this run, so extraction focused on the highest-confidence source discovered.

## Suggestions for v5
- Add direct site search endpoints per domain (e.g., `site:drive.com.au "fuel price board"`, `site:whichcar.com.au "petrol prices"`) with broader year ranges.
- Parse article structured data (`application/ld+json`) for additional image variants beyond the hero image.
- Prioritize pages mentioning specific gap brands (Costco, Metro, OTR, Liberty, 7-Eleven, Puma) to improve brand balance.
