# Scrape Report: v4 Slot 5 — YouTube Thumbnails (Gap Brands)

## Summary
- **Images saved:** 17
- **Images rejected:** 0
- **Brands covered:** metro, liberty, seven_eleven, puma
- **Hit rate by source:** ytthumb → 17 saved / 17 attempted (100%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| YouTube query: `Metro Petroleum Punchbowl` | success | 2 | Captured Metro-branded station/news thumbnails with visible bowser sign context |
| YouTube query: `Metro Petroleum fuel` | success | 2 | Added Metro-related Australian station thumbnails |
| YouTube query: `Puma Epping fuel` | success | 1 | Direct Puma Epping thumbnail |
| YouTube query: `Puma service station Australia` | success | 2 | Added Puma station thumbnails (QLD/NSW) |
| YouTube query: `7 Eleven Caboolture fuel` | success | 3 | Added multiple 7-Eleven fuel thumbnails |
| YouTube query: `7 eleven petrol station Australia` | success | 2 | Added AU 7-Eleven station thumbnails |
| YouTube query: `7-Eleven fuel app Australia` | success | 1 | Added app/demo thumbnail showing fuel price context |
| YouTube query: `Liberty petrol station Australia` | success | 4 | Added Liberty-gap thumbnails from AU fuel news coverage |

## What Worked
- Parsing YouTube search result pages for `"videoId"` values worked reliably.
- `img.youtube.com/vi/<VIDEO_ID>/maxresdefault.jpg` produced valid thumbnails in all saved cases.
- Mandatory validation checks (MIME image + size > 5KB) filtered out non-image/placeholder risk.

## What Didn't Work
- `yt-dlp ytsearch:` returned no results in this environment for these queries.
- DuckDuckGo HTML search path did not reliably return parsable YouTube links here.

## Suggestions for v5
- Continue Slot 5 with deeper locality queries (e.g., suburb + brand + `servo`).
- Add more night-focused terms per brand (`night`, `LED`, `dusk`) to improve lighting diversity.
- Expand Liberty/Metro with state-specific queries (`NSW`, `VIC`, `QLD`) and year filters (`2025`, `2026`).
