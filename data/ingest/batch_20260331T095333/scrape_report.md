# Scrape Report: v4 Slot 6 — National News Sites

## Summary
- **Images saved:** 15
- **Images rejected:** 1 (invalid combined `srcset` URL returned HTTP 400)
- **Brands covered:** independent (brand not explicitly visible in metadata), mixed national coverage
- **Hit rate by source:**
  - 7news.com.au → 13 saved / 13 attempted (100%)
  - 9news.com.au → 2 saved / 3 attempted (66.7%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `"petrol price" board site:7news.com.au` (discovery query) | success | 0 direct downloads | Used to discover article URLs; downloads came from article/CDN URLs below |
| https://7news.com.au/news/israel-iran-war-drivers-queue-across-australia-amid-petrol-price-fears-but-true-bowser-pain-could-be-10-days-away-c-21821049 | success | 3 | Multiple valid article image assets |
| https://7news.com.au/news/unprecedented-petrol-price-hike-for-queensland-drivers-before-christmas-slammed-by-racq-c-21064396 | success | 1 | Valid lead image captured |
| https://7news.com.au/news/iran-israel-and-us-war-australian-drivers-warned-of-petrol-price-hike-as-rationing-fears-loom-c-21874857 | success | 3 | PNG/JPG assets available, validated |
| https://7news.com.au/news/triple-threat-looms-as-petrol-price-surge-tipped-to-increase-inflation-interest-rates-amid-middle-east-conflict-c-21896363 | success | 3 | Valid 16:9 article assets |
| https://7news.com.au/news/fuel-retailers-slammed-over-petrol-price-hikes-amid-israel-iran-conflict-in-the-middle-east-c-21833919 | success | 3 | Valid 16:9 article assets |
| https://www.9news.com.au/national/victoria-daily-fuel-price-caps/30128357-747a-4c09-a38f-68c1539e17a7 | partial | 2 | Two valid image URLs saved; one malformed combined `srcset` URL rejected (HTTP 400) |

## What Worked
- National-news article pages exposed direct CDN image assets suitable for download.
- 7news article pages had high-quality, large image assets (>50KB in most cases), with strong hit rate.
- File verification workflow (`file` + size threshold) cleanly filtered non-image/invalid URLs.

## What Didn't Work
- Search-engine scraping endpoints were noisy and inconsistent for direct URL extraction.
- Some 9news extracted strings were combined `srcset` fragments, not single downloadable image URLs.
- Not all article images can be guaranteed to contain readable fuel labels/prices without manual visual QA.

## Suggestions for v5
- Add a post-download visual pass (or automated OCR precheck) to reject non-sign images before ingest.
- Continue Slot 6 on additional national outlets from prompt list (`news.com.au`, `abc.net.au`, `adelaidenow.com.au`) with direct article parsing.
- Prioritize brand-targeted national stories (`Costco fuel`, `OTR fuel`, `Metro Petroleum`) to close critical brand gaps.
