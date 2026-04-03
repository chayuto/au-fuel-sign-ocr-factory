# Scrape Report: v4 Slot 11 — Brand Corporate & Franchise Sites

## Summary
- **Images saved:** 13
- **Images rejected:** 3 (non-target/icon-marker assets from initial extraction pass)
- **Brands covered:** otr, metro, united, seven_eleven
- **Hit rate by source:**
  - otr.com.au → 6 saved / 6 attempted (100%)
  - metropetroleum.com.au → 2 saved / 2 attempted (100%)
  - unitedpetroleum.com.au → 3 saved / 3 attempted (100%)
  - 7eleven.com.au → 2 saved / 2 attempted (100%)
  - costco.com.au → 0 saved / 0 attempted (no usable station photo assets discovered on fuel page)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| https://www.otr.com.au/ | success | 1 | Station exterior image found and downloaded |
| https://www.otr.com.au/locations/ | success | 5 | Multiple station/location hero images with fuel context |
| https://www.metropetroleum.com.au/ | success | 2 | Metro station hero images downloaded |
| https://www.unitedpetroleum.com.au/ | success | 3 | United homepage fuel/station hero images downloaded |
| https://www.7eleven.com.au/fuel/our-fuels.html | success | 2 | Fuel-related hero assets downloaded |
| https://www.costco.com.au/fuel | partial | 0 | Fuel page returned no usable station-sign image assets |
| https://www.metropetroleum.com.au/store-locator/ | failed | 0 | 404 |
| https://www.unitedpetroleum.com.au/locations/ | failed | 0 | 404 |

## What Worked
- OTR locations page provided high-resolution station exterior photos with strong fuel branding context.
- Metro and United homepages exposed direct JPG hero assets in public paths.
- 7-Eleven fuel page exposed direct DAM image URLs suitable for download.
- Mandatory verification checks (file type + size > 5KB) succeeded for all saved files.

## What Didn't Work
- Costco fuel page did not expose direct downloadable station/fuel-sign images in accessible markup.
- Some extracted URLs were UI/icon assets and were rejected.
- A few likely location endpoints for Metro/United returned 404.

## Suggestions for v5
- For Costco, target media/press releases and external news coverage of Costco fuel locations rather than main fuel landing page.
- For OTR, continue deeper crawl of `/locations/` pagination and suburb-specific pages for additional unique station facades.
- For Metro/United, use press/news pages and franchise announcements to find more station exterior photos with price pylons.
- Add manual visual pass for strict readability filtering (fuel type text + price digits) before labeling queue ingestion.
