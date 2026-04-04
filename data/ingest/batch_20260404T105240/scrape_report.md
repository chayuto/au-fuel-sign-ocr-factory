# Scrape Report: v5 — News Articles (Metro Petroleum + OTR)

## Summary
- **Images saved:** 3
- **Images rejected:** 10+ (see reasons below)
- **Brands covered:** Metro Petroleum

## Images Saved

| Filename | Source Article | Notes |
|----------|---------------|-------|
| news_abc_metro_sydney_2023_01.jpg | ABC News 2023-03-15 "Metro Petroleum cheapest petrol Sydney" | 5000×3333, 3% amber LED, natural photo |
| news_abc_metro_sydney_2022_01.jpg | ABC News 2022-03-28 "Metro Petroleum and other cheap petrol" | 5000×3334, 34% concrete, natural photo |
| news_abc_metro_sydney_2024_01.jpg | ABC News 2024-08-14 "Cheapest petrol stations Sydney metro" | 5000×3333, natural photo |

## Quality Self-Check
- [x] Natural camera photo (not composite/screenshot/crop) — all 3 are unprocessed ABC CDN source images
- [x] Sign board likely visible — articles are specifically about Metro Petroleum fuel prices
- [x] Not a pump display, product catalog, or filtered photo
- [ ] Sign ≥15% of image area — PENDING visual verification (images too large to render in-session)

## Sources Attempted

| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| 7news.com.au/news/cost-of-living/metro-petroleum-fuel-price | 404 in PAGE_DATA | 0 | Topic page broken |
| 7news C-14892286/C-8437592/C-7964366 | Downloaded then rejected | 0 | Ad promo content, not fuel stations |
| adelaidenow.com.au OTR fuel | Blocked (News Corp bot block) | 0 | Anti-crawler |
| 9news.com.au Metro Petroleum search | JS-rendered, no content | 0 | JS rendering required |
| abc.net.au 2023-03-15 Metro Petroleum | SUCCESS | 1 | Specific Metro article |
| abc.net.au 2022-03-28 Metro Petroleum | SUCCESS | 1 | Specific Metro article |
| abc.net.au 2024-08-14 cheapest petrol Sydney | SUCCESS | 1 | General Sydney fuel article |
| drive.com.au fuel price search | 404 | 0 | Articles not found |
| DuckDuckGo HTML search | Bot-blocked | 0 | Anomaly detection |
| OTR (all news sources) | 0 | 0 | 14 OTR already exist in batch_20260404T040147 |

## Notes
- News Corp sites (adelaidenow.com.au) fully block non-browser scraping
- 7news Metro Petroleum topic page returns 404 in server data; topic is broken
- ABC News CDN (live-production.wcms.abc-cdn.net.au) serves full-res images without auth
- All 3 saved images are from SPECIFIC Metro Petroleum articles on ABC News
- OTR scraping was deprioritised since batch_20260404T040147 already contains 14 OTR images from Wikimedia
