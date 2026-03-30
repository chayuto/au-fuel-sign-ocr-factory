# Labeling Candidates — 2026-03-31

30 images validated by 2-pass Haiku screening (screen + validate). All confirmed to have
readable fuel price signs with at least one price in XXX.X format, at least one fuel type
label, and sign occupying >10% of the image. Ready for Sonnet labeling with visual QA.

## Screening Stats

| Stage | Input | Output | Rejection Rate |
|-------|-------|--------|---------------|
| Ingest (7 PRs) | 84 raw | 82 unique | 2 dups (SHA-256 + pHash) |
| Original pending | 168 | — | — |
| Haiku Screen (pass 1) | 250 total | 105 kept | 58% rejected |
| Haiku Validate (pass 2) | 105 | **30 confirmed** | 71% false positives caught |
| **Overall** | **250 images** | **30 ready** | **88% filtered out** |

## Source Quality Analysis

| Source | Screened | Kept | Hit Rate | Notes |
|--------|----------|------|----------|-------|
| Albert Smith (mfr) | ~40 | 5 | 12% | Professional pylon photos, many are station overviews |
| Wikimedia (wiki) | ~100 | 21 | 21% | Mixed quality, best source overall |
| News (news) | ~10 | 3 | 30% | Targeted articles, decent hit rate |
| Flickr group | ~30 | 0 | 0% | All heritage/vintage — completely useless |
| Free stock (free) | 1 | 1 | 100% | Single good image |
| YouTube thumbnails | 7 | 2* | 29% | Good for critical brands (7-Eleven, OTR) |
| Gov data (govau) | 30 | 2* | 7% | Mostly Google Street View thumbnails, too distant |
| Mapillary | 12 | 0 | 0% | Dashcam images, never close enough |
| Social media | 5 | 0 | 0% | Promo banners, not station photos |
| Real estate | 17 | 0 | 0% | Property/pump shots, no price signs |
| Forums | 8 | 1* | 12% | Mixed — some pizza flyers, some real stations |

*Some YouTube/gov/forum images confirmed in first screening but rejected in validation (prices not readable enough).

## Candidates by Brand

| Brand | Count | Images |
|-------|-------|--------|
| BP | 5 | bp_ballina_pylon, bp_caboolture, bp_geelong, 9news_bp, wa_nedlands_bp |
| Caltex/Woolworths | 4 | caltex_northlakes, 3x woolworths (curbside, generic, margate) |
| Westside | 4 | 4x doonside NSW |
| Independent | 4 | gascoyne_junction, jerramungup, york, unsplash |
| Puma | 2 | truganina_vic, morven_qld |
| Shell | 2 | bright_vic, leonora_wa |
| Mobil | 2 | mobi_pylon, leeton_mccafe |
| Coles Express | 1 | wallsend_nsw |
| United | 1 | medlow_nsw |
| Metro | 1 | citynews_canberra |
| Atlas | 1 | atlas_fuel_featured |
| Unknown | 3 | 9news_priceboard, wa_preston_beach, wa_yalgoo |

## Critical Gap Impact

| Brand | Before | After Labeling | Change |
|-------|--------|----------------|--------|
| Metro | 1 | 2 | +1 (still critical) |
| Costco | 0 | 0 | No images passed validation |
| OTR | 2 | 2 | YouTube/forum images failed validation |
| Liberty | 4 | 4 | Gov image failed validation |
| Independent | 7 | 11 | +4 |

**Costco remains at zero.** Mapillary, gov data, social media, and forums all failed to produce
usable Costco images. Need a different strategy — possibly manual photography or Google Maps
Place Photos API with API key.

## How to Launch Labeling

```bash
# Sonnet labeling — 1 image per agent, sequential or 5-8 parallel
# Use the fuel-sign-labeler skill Phase 2
```

The 30 images will add ~15-20% more training data (172 → ~200 labeled images).
Some may still be skipped by Sonnet if prices turn out to be unreadable at annotation time.
