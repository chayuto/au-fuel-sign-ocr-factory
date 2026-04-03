# Scrape Report: v4 Slot 10 — Signage Manufacturers (New Companies)

## Summary
- **Images saved:** 0
- **Images rejected:** 4
- **Brands covered:** none
- **Hit rate by source:**
  - Bartco → 0 saved / 2 attempted (0%)
  - JCDecaux AU → 0 saved / 2 attempted (0%)
  - Other target manufacturer domains → 0 saved / 0 attempted (unreachable or parked)

## Sources Attempted

| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| https://vantageled.com.au | failed | 0 | DNS/connection failed from sandbox (`curl` code 000). |
| https://ledcraft.com.au | failed | 0 | DNS/connection failed from sandbox (`curl` code 000). |
| https://nationalsignindustries.com.au | failed | 0 | DNS/connection failed from sandbox (`curl` code 000). |
| https://programmedsigns.com.au | failed | 0 | DNS/connection failed from sandbox (`curl` code 000). |
| https://signfoundry.com.au | failed | 0 | DNS/connection failed from sandbox (`curl` code 000). |
| http://megasigns.com.au | failed | 0 | Domain resolves but serves parked/ad-redirect page, no usable source media. |
| https://bartco.com.au | success | 0 | Site accessible; sampled assets are road-work/traffic products, not fuel station price sign boards. |
| https://www.jcdecaux.com.au + sitemap crawl | success | 0 | Site accessible, but sampled campaign/media assets did not show readable fuel price sign boards. |

## Rejection Log (attempted downloads)

| Candidate | Validation | Rejection reason |
|-----------|------------|------------------|
| `https://bartco.com.au/wp-content/uploads/2025/04/bartco-feature-image.png` | valid PNG, >5KB | Corporate/brand image; no fuel price sign board with readable price+label. |
| `https://bartco.com.au/wp-content/uploads/2024/10/VMC-5C-C-Sign-2.jpg` (sampled from products page) | valid JPG, >5KB | Traffic/VMS equipment, not petrol station price signage context. |
| `https://d3k1k88y44k0jy.cloudfront.net/.../COTY_Winner_JCD Homepage banner...jpg` | valid JPG, >5KB | Homepage hero/banner unrelated to fuel station price boards. |
| `https://d3k1k88y44k0jy.cloudfront.net/.../partnerservices-image02-cleaning.jpg` | valid JPG, >5KB | Maintenance service photo, no readable fuel type/price sign board. |

## Dedup Checks
- Ran keyword-based dedup checks across both paths before download attempts:
  - `data/ingest/`
  - `data/tmp/`
- Keywords checked: `vantageled`, `megasigns`, `ledcraft`, `bartco`, `nationalsignindustries`, `programmedsigns`, `signfoundry`, `jcdecaux`.
- No collisions found for candidate naming keywords.

## What Worked
- Bartco and JCDecaux domains were reachable and parsable.
- JCDecaux `robots.txt` revealed sitemap endpoint; sitemap crawl was possible from `www` host.
- Asset extraction and file-type/size validation workflow worked.

## What Didn't Work
- 5/8 target manufacturer domains were unreachable from this environment.
- 1/8 domain (`megasigns.com.au`) appears parked (ad/redirect content, no real manufacturer media).
- Reachable sources (Bartco, JCDecaux) did not yield images meeting mandatory fuel-sign criteria.

## Suggestions for v5
- Replace unreachable/parked manufacturer targets with currently live AU fuel-sign vendors.
- Add stricter pre-filter: prioritize pages explicitly mentioning "petrol", "fuel price sign", "service station" before downloading assets.
- Consider direct station signage fabricators with documented petrol pylon portfolios and public case-study galleries.
- Pair Slot 10 with Slot 6/7 fallback in the same run when manufacturer yield is zero.
