# Scrape Prompt: Australian Fuel Station Price Sign Images (v4 — Targeted Gap Fill)

## Your Mission

You are a scraping agent. Find and download real-world images of **Australian fuel station price sign boards**. These train a YOLO object detection model that reads fuel prices from photos.

**Why v4?** Previous rounds scraped ~1000 images but only 167 had usable price signs (17% hit rate). v4 focuses on **proven high-yield sources** and **critical brand gaps**. Each slot is a self-contained task — pick ONE slot and go deep.

## Current Dataset Gaps (Priority Order)

| Brand | Have | Need | Priority |
|-------|------|------|----------|
| **Costco** | **0** | 10+ | CRITICAL — zero training data |
| **Metro** | **2** | 10+ | CRITICAL — only 2 images |
| **OTR** | **2** | 10+ | CRITICAL — SA/VIC only |
| **Liberty** | **4** | 10+ | HIGH — underrepresented |
| **7-Eleven** | **7** | 15+ | MEDIUM — need more variety |
| **Puma** | **8** | 12+ | MEDIUM |
| Night/dusk shots | ~15% | 30%+ | HIGH — LED signs look different at night |
| Rain/overcast | ~10% | 20%+ | MEDIUM — affects detection |

**Well-represented (don't prioritize):** Caltex (40), BP (24), Shell (20), United (17), Ampol (15), Independent (14), Mobil (13)

## What Makes a GOOD Image

ALL of these must be true:
- A fuel price **sign board** is visible (pylon, canopy fascia, or wall panel)
- At least one **fuel type label** is readable (e.g., "Unleaded", "Diesel", "E10")
- At least one **price** is readable (LED digits or printed, format: XXX.X cents/litre)
- Sign occupies **>10% of image area** (not a distant street-level shot)

## Source Quality Ratings (Learned from v1-v3)

### HIGH YIELD (>20% usable) — Focus here
| Source | Hit Rate | Notes |
|--------|----------|-------|
| **News articles** | ~30% | Targeted fuel price stories have sign close-ups |
| **YouTube thumbnails** | ~29% | Especially for gap brands (7-Eleven, OTR) |
| **Wikimedia Commons** | ~21% | Best volume source; many categories untapped |
| **Signage manufacturers** | ~12% | Professional pylon/LED photos |
| **Automotive blogs** | ~15% | Fuel price comparison articles |
| **Forums** | ~12% | Mixed — some real station photos among noise |

### ZERO YIELD — Do NOT waste time on these
| Source | Why it fails |
|--------|-------------|
| Mapillary street-level | Dashcam images never close enough to read prices |
| Social media (FB/Insta) | All promo banners, not station photos |
| Real estate listings | Property/pump architecture shots, no price signs |
| Flickr heritage groups | 100% vintage/retro, zero modern signs |
| Google Image Search | No API, can't extract |
| Stock photo sites | 403 Forbidden |
| Pinterest/Reddit | Auth walls, no results |
| Google Maps Place Photos | Requires API key (we don't have one) |

---

## SLOT 1 — Wikimedia: Gap Brands

Target Wikimedia categories and searches specifically for underrepresented brands.

### Categories to Crawl
```
Category:On_The_Run_(convenience_stores)
Category:7-Eleven_in_Australia
Category:Puma_Energy
Category:Liberty_Oil
Category:Costco_Australia
```

### Search Queries (Wikimedia API)
```
# https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=QUERY&srnamespace=6&format=json
"OTR fuel" OR "On The Run fuel"
"Metro Petroleum"
"Liberty fuel" OR "Liberty Oil"
"Costco fuel Australia"
"7-Eleven fuel Australia"
"Puma Energy Australia"
```

### Download via API
```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&titles=File:FILENAME&prop=imageinfo&iiprop=url&format=json"
curl -sL -o "$BATCH_DIR/wiki_{brand}_{location}.jpg" "DIRECT_URL"
```

**IMPORTANT:** Verify downloaded file is an actual image (not JSON/HTML error). Check `file` command output and size > 5KB.

---

## SLOT 2 — Wikimedia: State-by-State Deep Dive

Crawl state-level Wikimedia categories not yet fully scraped.

### Categories
```
Category:Petrol_stations_in_South_Australia    ← OTR territory
Category:Petrol_stations_in_Queensland         ← Puma territory
Category:Petrol_stations_in_Western_Australia   ← Liberty/independent
Category:Petrol_stations_in_Tasmania
Category:Petrol_stations_in_Northern_Territory
Category:Fuel_prices_in_Australia
Category:Petrol_stations_in_the_Australian_Capital_Territory
```

Focus on states with gap brands: SA (OTR), QLD (Puma), WA (Liberty/independent).

### Already Scraped (skip these)
```
Category:Petrol_stations_in_New_South_Wales     ← mostly done
Category:Petrol_stations_in_Victoria            ← mostly done
Category:Shell_petrol_stations                  ← well-represented
Category:BP_petrol_stations                     ← well-represented
```

---

## SLOT 3 — Wikimedia: Night & Weather Conditions

Specifically search for night/dusk/rain station photos to fill the lighting gap.

### Search Queries
```
"petrol station night" Australia
"fuel station dusk"
"servo night" Australia
"fuel price LED night"
"petrol station rain" Australia
"service station evening"
```

### Categories
```
Category:Night_photographs_in_Australia    ← filter for fuel stations
Category:Photographs_taken_at_night        ← search within for "fuel" "petrol" "servo"
```

---

## SLOT 4 — YouTube Thumbnails: Costco & OTR

YouTube fuel price videos have high thumbnail hit rate (~29%). Focus on the hardest gaps.

### Thumbnail URL Pattern
```bash
# Find video IDs via web search, then:
https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg
# Fallback if maxres unavailable (< 10KB = placeholder):
https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg
```

### Search Queries
```
"Costco fuel" Australia 2024 2025 2026
"Costco petrol" price Australia
"OTR fuel prices" Adelaide
"On The Run fuel" price
"cheapest fuel Australia" Costco
"Costco fuel queue" Australia
```

---

## SLOT 5 — YouTube Thumbnails: Other Gap Brands

Same technique, different brand focus.

### Search Queries
```
"Metro Petroleum" prices Sydney
"Liberty fuel" Australia prices
"7-Eleven fuel" Australia prices
"Puma fuel" Australia
"cheapest fuel" sign board Australia
"fuel price war" Australia servo
"petrol prices" night sign
"diesel prices" Australia servo LED
```

---

## SLOT 6 — National News Sites

Fuel price articles from major Australian news outlets. ~30% hit rate — the best source type.

### Search Queries
```
"fuel price" sign photo site:9news.com.au
"petrol price" board site:7news.com.au
"fuel prices" sign site:abc.net.au
"Costco fuel" price site:news.com.au
"cheapest fuel" price board Australia 2025 2026
"fuel price war" servo sign Australia
"petrol prices" record high sign board
"diesel price" sign Australia
"OTR fuel" price site:adelaidenow.com.au
"Metro Petroleum" price site:smh.com.au
```

### CDN Domains
```
News Corp: content.api.news, cdn.newsapi.com.au
Nine/Fairfax: static.ffx.io, images.nine.com.au
Seven West: images.perthnow.com.au
ABC: live-production.wcms.abc-cdn.net.au
```

---

## SLOT 7 — Regional & Local News

Regional outlets cover local fuel prices with close-up sign photos. Good for rural/outback diversity.

### Search Queries
```
"fuel price" sign site:canberratimes.com.au
"petrol price" servo site:thewest.com.au
"fuel prices" site:adelaidenow.com.au
"fuel price" sign site:couriermail.com.au
"petrol price" servo site:examiner.com.au
"fuel price" site:ntnews.com.au
"fuel price" site:themercury.com.au
"petrol price" site:geelongadvertiser.com.au
"fuel price" site:townsvillebulletin.com.au
"petrol price" site:cairnspost.com.au
"fuel" "price sign" site:countrynewsgroup.com.au
```

Focus on SA (OTR), NT/WA (rural/independent), QLD (Puma).

---

## SLOT 8 — Automotive & Motoring Blogs

Car review sites cover fuel prices. ~15% hit rate.

### Targets
```
"fuel price" sign site:carsguide.com.au
"petrol price" board site:drive.com.au
"fuel price" site:caradvice.com.au
"fuel prices" site:whichcar.com.au
"servo price" sign site:motoring.com.au
"fuel price comparison" Australia sign photo
"cheapest fuel" sign site:racv.com.au
"fuel prices" site:nrma.com.au
```

---

## SLOT 9 — Forums (Whirlpool / OzBargain)

Mixed content (~12% hit rate) but sometimes has user-uploaded station photos.

### Search Queries
```
site:whirlpool.net.au "fuel price" sign photo
site:forums.whirlpool.net.au "servo" "price board"
site:ozbargain.com.au "fuel price" photo servo
site:whirlpool.net.au "Costco fuel"
site:whirlpool.net.au "Metro Petroleum"
site:ozbargain.com.au "cheapest fuel" sign
```

**Warning:** High noise — pizza flyers, memes, and unrelated images mixed in. Verify every download visually before saving.

---

## SLOT 10 — Signage Manufacturers (New Companies)

Professional fuel sign photos. Already scraped: Albert Smith, Sydney LED, CV Media, Signtronics, Daktronics, PetroLED, Link Signs, WiPath.

### New Targets
| Company | URL | Focus |
|---------|-----|-------|
| Vantage LED | vantageled.com.au | LED fuel signs |
| Mega Signs | megasigns.com.au | Perth — Liberty/independent |
| LED Craft | ledcraft.com.au | LED price displays |
| Bartco | bartco.com.au | LED variable message signs |
| National Sign Industries | nationalsignindustries.com.au | Pylon/totem |
| Programmed Signs | programmedsigns.com.au | Fuel signage |
| Sign Foundry | signfoundry.com.au | Various |
| JCDecaux AU | jcdecaux.com.au | Fuel station signage |

---

## SLOT 11 — Brand Corporate & Franchise Sites

Some fuel brands have station locator pages or media galleries with sign images.

### Targets
```
costco.com.au/fuel                    ← Costco fuel page, may have station photos
otr.com.au                            ← On The Run, check media/gallery
metropetroleum.com.au                 ← Metro, check locations/media
liberty.com.au                        ← Liberty Oil
puma.com.au/en-au                     ← Puma Energy Australia
7eleven.com.au/fuel                   ← 7-Eleven fuel page
united.com.au                         ← United Petroleum
```

Also check press releases and media kits — they sometimes embed station exterior photos with visible price signs.

---

## SLOT 12 — Fuel Price Comparison Apps & Review Sites

Fuel comparison platforms sometimes embed station photos.

### Targets
```
petrolspy.com.au                      ← User-submitted station photos
fuelmap.com.au                        ← Station listings with images
motormouth.com.au                     ← Fuel price tracker
"fuel price" site:productreview.com.au ← Station reviews with photos
"servo" review site:google.com/maps   ← Google Maps reviews (public, no API needed)
```

### Google Maps Review Approach (No API Key Needed)
Search for individual stations on Google Maps web. User reviews sometimes include photos of price signs. Extract image URLs from the page source.
```
Search: "Costco fuel Docklands" → Google Maps → Photos tab → user photos
Search: "Metro Petroleum Bankstown" → Google Maps → Photos tab
```

---

## Scope & Guardrails

1. **Write ONLY to your batch directory** (see "Where to Save")
2. **Do NOT modify existing files** — no manifests, logs, configs, scripts, code
3. **Do NOT `git push`** — commit locally, main agent reviews before push
4. **Do NOT run training, labeling, or build scripts**
5. **Do NOT write to `data/tmp/`** — off-limits
6. **Verify each download** — file size > 5KB, actual image (not HTML/JSON error)
7. **Follow naming convention** — `{source}_{brand}_{location}_{detail}.{ext}`
8. **Dedup before every download** (see Dedup section)

## Dedup (MANDATORY)

Before downloading ANY image:

```bash
# Check existing files by keyword
find data/ingest/ -type f -iname "*KEYWORD*" 2>/dev/null
find data/tmp/ -type f -iname "*KEYWORD*" 2>/dev/null
```

Check **both** `data/ingest/` and `data/tmp/`. If a similar file exists, **skip it**.

After your batch, the main agent runs 3-level dedup (filename, SHA-256, pHash) to catch anything you missed.

## Where to Save

```bash
BATCH_DIR="data/ingest/batch_$(date -u +%Y%m%dT%H%M%S)"
mkdir -p "$BATCH_DIR"
```

Write ONLY to your `$BATCH_DIR`. Keep it flat — no subdirectories.

## File Naming

```
{source}_{brand}_{location}_{detail}.{ext}

Sources: wiki, ytthumb, news, mfr, web, forum, brand, review
Brands: shell, bp, ampol, caltex, seven_eleven, united, costco, liberty, puma, metro, mobil, otr, independent

Examples:
  wiki_otr_adelaide_sa_01.jpg
  ytthumb_costco_epping_vic.jpg
  news_9news_metro_sydney.jpg
  mfr_vantageled_fuel_sign_01.jpg
  brand_costco_docklands_vic.jpg
  forum_whirlpool_liberty_perth.jpg
  review_petrolspy_otr_adelaide.jpg
```

## Commit Pattern

```bash
git add "$BATCH_DIR"/*.jpg "$BATCH_DIR"/*.png "$BATCH_DIR"/*.jpeg "$BATCH_DIR"/scrape_report.md
git commit -m "scrape: add N images from SOURCE — BRANDS covered

batch: $BATCH_DIR
slot: SLOT_N"
```

Commit in batches of 10-30 images. **Do NOT `git push`**.

## Findings Report (MANDATORY)

Write `scrape_report.md` in your batch directory after completing the scrape.

```markdown
# Scrape Report: v4 Slot N — [Source Name]

## Summary
- **Images saved:** N
- **Images rejected:** N (with reasons)
- **Brands covered:** list
- **Hit rate by source:** source → N saved / N attempted (%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| ... | success/failed | N | what happened |

## What Worked
- ...

## What Didn't Work
- ...

## Suggestions for v5
- Untapped leads, new URLs, strategy ideas
```

## Slot Summary

| Slot | Source | Focus | Expected Yield |
|------|--------|-------|---------------|
| 1 | Wikimedia — gap brands | Costco/Metro/OTR/Liberty/7-Eleven | Medium |
| 2 | Wikimedia — state deep dive | SA, QLD, WA, TAS, NT | Medium-High |
| 3 | Wikimedia — night/weather | Night, dusk, rain shots | Low-Medium |
| 4 | YouTube thumbnails — Costco/OTR | Hardest gap brands | Medium |
| 5 | YouTube thumbnails — other gaps | Metro/Liberty/7-Eleven/Puma | Medium |
| 6 | National news sites | All brands, price stories | High |
| 7 | Regional news | Rural/outback, SA/WA/NT | Medium |
| 8 | Automotive blogs | Fuel price articles | Medium |
| 9 | Forums | User-uploaded station photos | Low |
| 10 | Signage manufacturers | Professional sign photos | Low-Medium |
| 11 | Brand corporate sites | Direct from brand websites | Low |
| 12 | Fuel comparison/review sites | PetrolSpy, Google Maps reviews | Medium |

**Pick your slot and go deep.** Quality over quantity — 10 usable gap-brand images beat 100 distant BP shots.
