# Scrape Report: v4 Slot 7 — Regional & Local News

## Summary
- **Images saved:** 11
- **Images rejected:** 0 (all extracted og:image assets passed validation)
- **Brands covered:** seven_eleven, independent
- **Hit rate by source:**
  - canberratimes.com.au → 10 saved / 10 attempted (100%)
  - examiner.com.au → 1 saved / 1 attempted (100%)
  - adelaidenow.com.au → 0 saved / 0 attempted (search blocked/403 in this environment)
  - couriermail.com.au → 0 saved / 0 attempted (search blocked/403 in this environment)
  - ntnews.com.au → 0 saved / 0 attempted (search blocked/403 in this environment)
  - thewest.com.au → 0 saved / many URLs scanned, no clearly fuel-price-sign image candidates selected
  - townsvillebulletin.com.au → 0 saved / search page accessible but no extractable matching story links in static HTML
  - cairnspost.com.au → 0 saved / search page accessible but no extractable matching story links in static HTML

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `https://www.canberratimes.com.au/sitemap-news.xml` + fuel/petrol filters | success | 6 | yielded fresh fuel-crisis stories with og:image |
| `https://www.canberratimes.com.au/sitemap.xml` + fuel/petrol filters | success | 4 | older fuel-price stories with usable hero photos |
| `https://www.examiner.com.au/sitemap.xml` + fuel filters | partial success | 1 | one recent fuel-crisis story located |
| `https://www.thewest.com.au/search?query=fuel+prices` | partial | 0 | many links, but no confident fuel price sign shots selected |
| `https://www.adelaidenow.com.au/search-results?q=fuel%20prices` | failed | 0 | HTTP 403 |
| `https://www.couriermail.com.au/search-results?q=fuel%20prices` | failed | 0 | HTTP 403 |
| `https://www.ntnews.com.au/search-results?q=fuel%20prices` | failed | 0 | HTTP 403 |
| `https://www.townsvillebulletin.com.au/search-results?q=fuel%20prices` | partial | 0 | no fuel result payload in static HTML |
| `https://www.cairnspost.com.au/search-results?q=fuel%20prices` | partial | 0 | no fuel result payload in static HTML |

## What Worked
- Pulling article URLs from regional-news XML sitemaps was much more reliable than general web search.
- Extracting `og:image` from each article gave direct, high-resolution JPEG assets.
- Mandatory validation worked: each saved file is >5KB and `file --mime-type` reports `image/jpeg`.

## What Didn't Work
- DuckDuckGo query automation hit anti-bot challenges for several regional-source queries.
- Some News Corp regional search endpoints returned 403 from this environment.
- Some accessible search pages rendered no useful article result links in static HTML (likely JS-rendered).

## Suggestions for v5
- Use sitemap-first strategy for News Corp regional domains (`/sitemap.xml`, `/news-sitemap.xml`) instead of search pages.
- Add manual visual triage step to score sign size/readability before ingest to improve effective hit rate.
- Prioritize SA-specific sources for OTR gap fill (e.g., adelaidenow when access is available, plus direct OTR-related local outlets).
- Pair regional slot with Slot 4/5 YouTube thumbnails for hard gap brands (Costco/OTR/Metro/Liberty).
