# Scrape Manifest — Tracking What's Been Scraped

**Purpose:** Prevent duplicate scraping across agents. Each agent checks this before starting.

## Completed Sources

| Source | Date Scraped | Agent | Images Found | Valid (with prices) | Notes |
|--------|-------------|-------|-------------|-------------------|-------|
| Wikimedia: Gasoline price boards/displays | 2026-03-29 | Agent 3 (initial) | 9 | 6 | AU images: Shell, Mobil, Ampol, Caltex, United |
| Wikimedia: Shell AU stations | 2026-03-29 | Shell agent | 20 downloaded | 11 (4A, 4B, 3C) | Good variety of sign types |
| Wikimedia: VIC petrol stations | 2026-03-29 | VIC agent | 31 | ~15 | Mix of modern and rural |
| Wikimedia: Caltex/Ampol AU | 2026-03-29 | Caltex/Ampol agent | 60 | ~25 | Extensive coverage |
| Wikimedia: NSW/QLD/WA stations | 2026-03-29 | State agents | ~50 | ~20 | Good regional variety |
| Wikimedia: BP AU stations | 2026-03-29 | Session 2 | 9 | ~5 | Port Hedland, Innisfail, Broome |
| Wikimedia: United Petroleum | 2026-03-29 | Session 2 | 4 | 2 | Brisbane price display, oil price hikes |
| Wikimedia: Ampol AU stations | 2026-03-29 | Session 2 | 8 + 6 subcats | ~5 | Apollo Bay, Nambour, Gosnells |
| Wikimedia: WA petrol stations | 2026-03-29 | Session 2 | 10 | ~4 | MobilPriceBoard.png notable |
| Wikimedia: Petrol station signs | 2026-03-29 | Session 2 | 5 AU of 64 | 3 | Mobil Albury, Mundrabilla, Nullarbor |
| Albert Smith Signs gallery | 2026-03-29 | Session 2 | 44 | ~30 | BP, Caltex, United, Puma, Mobil, Pacific, Matilda |
| Sydney LED Signs products | 2026-03-29 | Session 2 | 12 | 12 | LED digit product shots, 3 sizes |
| News articles (SBS, Carsales, CarExpert) | 2026-03-29 | Session 2 | 7 | 4 | Narrabri prices, BP diesel board, fuel pump |
| AAP Photos via regional news | 2026-03-29 | Session 2 | 3 | 1 | Fuel shortage/station photos |
| CV Media Signage | 2026-03-29 | Session 2 | 1 | 1 | OTR pylon sign |
| CarsGuide editorial | 2026-03-29 | Session 2 | 1 | 1 | BP station |
| Roboflow Universe (search) | 2026-03-29 | Agent 1 | 0 relevant AU | 0 | No AU fuel sign datasets exist |
| Kaggle / Open Images | 2026-03-29 | Agent 2 | 0 relevant | 0 | Only tabular CSV data on Kaggle |
| News sites direct crawl | 2026-03-29 | Agent 4 | Blocked | 0 | All AU news sites block crawlers |

## Failed Sources (Do Not Retry)

| Source | Reason |
|--------|--------|
| Flickr search | JS-rendered page, WebFetch gets empty HTML |
| Dreamstime | 403 Forbidden |
| AussieHerald | 403 Forbidden |
| Pinterest | Auth wall |
| eBay AU | Only Chinese manufacturer listings, no AU installations |
| Geograph.org.au | Zero results for fuel signs |
| Reddit | Zero results for fuel sign photos |
| Google Image Search | No API, can't extract thumbnail URLs |

## NOT YET SCRAPED — Available Sources

| Source | Est. Yield | License | Difficulty | Priority |
|--------|-----------|---------|------------|----------|
| Wikimedia: Ampol subcats (Chatswood, Concord, Granville, Prestons, Rosebery) | 10-20 | CC | Easy | HIGH |
| Wikimedia: 7-Eleven stores in AU | 5-15 | CC | Easy | HIGH |
| Wikimedia: Costco AU stores | 3-5 | CC | Easy | HIGH |
| Mapillary API (street-level, geo: AU fuel stations) | 50-200 | CC BY-SA 4.0 | Medium (need API key) | HIGH |
| Unsplash/Pexels CC0 fuel station photos | 5-20 | CC0 | Easy | MEDIUM |
| More signage manufacturers (Signtronics, Daktronics AU) | 10-30 | Portfolio | Easy | HIGH |
| More news articles (ABC, 7News, news.com.au) | 5-15 | Editorial | Medium | MEDIUM |
| Google Street View Static API | 200-500 | Google ToS | Hard (API key, costs) | LOW |
| Australian council DA images | 5-10 | Public record | Hard | LOW |

## Dedup Rules

- Before downloading, check filename against existing files in `data/tmp/` and `/tmp/wiki_*`
- Each agent is assigned a SPECIFIC source — no overlap
- Agent results go to `/tmp/wiki_{source}_results.json` or `data/tmp/`
- All validated images eventually copy to `data/raw/{batch}/` with `source_manifest.json`
