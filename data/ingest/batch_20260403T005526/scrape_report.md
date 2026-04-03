# Scrape Report: v4 Slot 12 — Fuel Comparison/Review Sites

## Summary
- **Images saved:** 0
- **Images rejected:** 4 (non-station/logo/video-thumbnail assets; no verifiable readable fuel sign board)
- **Brands covered:** none
- **Hit rate by source:**
  - petrolspy.com.au → 0 saved / 1 attempted (0%)
  - fuelmap.com.au → 0 saved / 1 attempted (0%)
  - motormouth.com.au → 0 saved / 1 attempted (0%)
  - productreview.com.au → 0 saved / 4 attempted assets (0%)
  - google.com/maps web pages → 0 saved / 4 attempted (0%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| https://petrolspy.com.au/map/latlng/-33.8688/151.2093 | success | 0 | Page loaded; no station-photo URLs exposed in static HTML |
| https://www.fuelmap.com.au/ | failed | 0 | Fetch failed from environment (connection failure) |
| https://www.motormouth.com.au/ | success | 0 | App shell loaded; no station-photo assets exposed |
| https://www.productreview.com.au/search?q=costco%20fuel | success | 0 | Extracted image assets were site/logo or generic video thumbnail; rejected |
| https://www.productreview.com.au/search?q=metro%20petroleum | success | 0 | Same as above; no usable sign-board photo located |
| https://www.productreview.com.au/search?q=7-eleven%20fuel | success | 0 | Same as above; no usable sign-board photo located |
| https://www.productreview.com.au/search?q=petrolspy | success | 0 | Same as above; no usable sign-board photo located |
| https://www.google.com/maps/place/Costco+Wholesale+Docklands/ | success | 0 | Returned JS-heavy page; no downloadable user-photo URLs extractable |
| https://www.google.com/maps/place/Costco+Epping/ | success | 0 | Same extraction limitation |
| https://www.google.com/maps/place/Metro+Petroleum+Bankstown/ | success | 0 | Same extraction limitation |
| https://www.google.com/maps/place/7-Eleven+Fuel+Docklands/ | success | 0 | Same extraction limitation |

## What Worked
- Confirmed access to PetrolSpy and ProductReview HTML content.
- Isolated candidate media URLs from ProductReview output, then rejected non-qualifying assets.

## What Didn't Work
- FuelMap was unreachable from this runtime.
- Google Maps web pages did not expose direct downloadable review-photo URLs in retrievable static HTML.
- Slot 12 sources in this run did not yield verifiable fuel price sign-board photos meeting quality criteria.

## Suggestions for v5
- Use browser-automation flow with authenticated/interactive Google Maps Photos tab to capture direct `lh3.googleusercontent.com/p/...` image links, then filter manually.
- Add additional Slot 12 sources with explicit public photo galleries (station-review pages that render image URLs server-side).
- Pair Slot 12 with targeted fallback slot (e.g., Slot 6 news) when hit rate remains zero after fixed attempt budget.
