# Scrape Prompt: Australian Fuel Station Price Sign Images (v2)

## Your Mission

You are a scraping agent. Your job is to find and download real-world images of **Australian fuel station price sign boards** — the pylon or wall-mounted signs that display fuel type labels and LED/printed prices. These images train a YOLO object detection model.

**You are collecting training data, not browsing.** Every image you save must contain a **visible fuel price sign with readable prices**. Station-only shots, pump closeups, brand logos without prices, historical photos without price boards — these are all waste. Be selective.

## Scope

**IMAGE SCRAPING only.** Find and download images. Nothing else.

You do NOT:
- Label, annotate, or draw bounding boxes on images
- Edit manifests, logs, or CSV files
- Run Python scripts (except curl/wget for downloads)
- Modify anything in `data/tmp/` — that directory is off-limits
- Touch any code, configs, or docs

If you're unsure whether something is in scope, it isn't. Just download images.

## Guardrails

These rules are non-negotiable:

1. **Write ONLY to your own batch directory** (see "Where to save" below)
2. **Do NOT modify any existing files** — no manifests, logs, configs, scripts, code
3. **Do NOT `git push`** — commit locally only, main agent reviews before push
4. **Do NOT run training, labeling, or build scripts** — download images only
5. **Do NOT write to `data/tmp/`** — that directory is off-limits
6. **Do NOT touch another agent's batch directory**
7. **Verify each download** — file size > 1KB, valid image format
8. **Follow naming convention** — `{source}_{brand}_{location}_{detail}.{ext}`
9. **Dedup before every download** (see Dedup section)

## What Makes a GOOD Image

A good image has ALL of these:
- A fuel price **sign board** is visible (pylon-mounted, canopy fascia, or wall panel)
- At least one **fuel type label** is readable (e.g., "Unleaded", "Diesel", "E10", "V-Power")
- At least one **price** is readable (LED digits or printed numbers, format: XXX.X cents/litre)
- The sign is large enough in frame to identify text (~>10% of image area)

### Ideal images (prioritize these)
- Close-up or medium shot of the price panel section
- Multiple fuel rows visible (3-6 entries)
- Clear, sharp, well-lit
- Variety: different brands, times of day, weather, angles

### Skip these (do NOT save)
- Fuel pumps/bowsers only (no price board)
- Station canopy/building without price sign
- Brand logo signs without price displays
- Historical photos (pre-2000) with no readable prices
- Product shots of LED digit modules without station context
- Signs too distant or blurry to read any text
- Duplicate/near-duplicate of an image already in the repo

## Target Brands (Australian)

| Brand | Priority | Notes |
|-------|----------|-------|
| **Costco** | **CRITICAL** | **Zero in dataset.** Distinctive canopy-mounted. Rare. |
| **Metro** | **CRITICAL** | **Zero in dataset.** Blue/red branding. |
| Shell | HIGH | Red LED on dark panel. Often co-branded Coles Express |
| BP | HIGH | Green LED on green panel |
| Ampol | HIGH | White/red LED on dark blue panel |
| Caltex | HIGH | Rebranding to Ampol. White/red on red or white |
| 7-Eleven | HIGH | Red/orange LED. Co-branded Mobil. Need more. |
| OTR | MEDIUM | White LED on red panel. SA/VIC only. Very light in dataset. |
| Liberty | MEDIUM | Red/amber LED on dark blue. Light in dataset. |
| United | MEDIUM | Red LED on blue panel |
| Puma | MEDIUM | Red/amber on dark panel |
| Mobil | MEDIUM | Red LED on blue panel |
| Independent | LOW | Varies widely |

## Scenario Gaps (High Priority)

These are underrepresented — actively seek them:
- **Night/dusk shots** with illuminated LED signs
- **Rain/overcast** weather conditions
- **Angled/perspective** views (not perfectly frontal)
- **Rural/outback** station signs (regional pricing)
- **Multiple signs** in one frame (competing stations)

---

## Slot System — READ THIS FIRST

You have been assigned a **SLOT number** (1-5). Your slot determines which sources you scrape. **Only use YOUR slot's sources.** This prevents multiple agents from downloading the same images.

If you were not given a slot number, default to SLOT 3 (news search — most varied).

---

## SLOT 1 — Wikimedia Commons: State Categories (VIC, QLD, SA)

Browse these Wikimedia Commons categories and download images with visible price signs:

```
Category:Petrol_stations_in_Victoria,_Australia    (~56 files)
Category:Petrol_stations_in_Queensland             (~53 files)
Category:Petrol_stations_in_South_Australia         (smaller)
```

**How to browse a category:** Fetch the category page via the Wikimedia API:
```
https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Petrol_stations_in_Victoria,_Australia&cmtype=file&cmlimit=100&format=json
```
This returns a JSON list of filenames. For each file, check if it's likely to contain a price sign (look for keywords like "price", "fuel", "petrol", brand names in the filename). Download promising ones and visually verify.

**Download pattern:**
```bash
curl -sL -o "$BATCH_DIR/wiki_{brand}_{location}.jpg" \
  "https://api.wikimedia.org/core/v1/commons/file/File:FILENAME/download"
```

The REST API (`api.wikimedia.org`) is more reliable than `Special:FilePath` which sometimes returns HTML error pages.

**Already in dataset (check dedup):** ~39 VIC files, ~15 QLD files, ~10 SA files. Many exist — dedup before every download.

---

## SLOT 2 — Wikimedia Commons: State + Brand Categories (NSW, WA, United, Puma)

Browse these categories:

```
Category:Petrol_stations_in_New_South_Wales        (~62 files)
Category:Petrol_stations_in_Western_Australia      (~28 files)
Category:United_Petroleum                          (check subcategories)
Category:Puma_petrol_stations_in_Australia         (~12 files)
```

**How to browse and download:** Same API pattern as Slot 1.

**Already in dataset:** ~14 NSW files, ~10 WA files. Many more remain in these categories.

---

## SLOT 3 — News Articles + Web Search

Search the web for Australian fuel price articles, then extract images from the articles. This is a two-step process.

**Step 1 — Search.** Use varied queries to avoid overlapping with other agents' past searches. Use ALL of these queries, not just the first one:

```
"petrol price sign" Australia 2025
"fuel price board" LED station Australia
"servo prices" pylon sign Queensland
"petrol station" price display Melbourne 2026
"fuel prices" sign board Sydney NSW
"diesel price" sign rural Australia
Costco fuel price Australia
Metro Petroleum station price sign
Liberty fuel station Australia price
OTR petrol price sign Adelaide
```

**Step 2 — For each article found:** Fetch the article page, find `<img>` tags or CDN image URLs, download images that show fuel price signs.

**CDN domains known to work:**
- ABC News: `live-production.wcms.abc-cdn.net.au`
- SBS: `sbs-au-brightspot.s3.ap-southeast-2.amazonaws.com`
- Carsales: `editorial.pxcrush.net`
- CarExpert: `images.carexpert.com.au`
- Yahoo News AU: accessible directly
- Regional newspapers (Bunbury Mail, etc.): `/images/transform/v1/crop/frm/`

**Download pattern:**
```bash
curl -sL -H "User-Agent: Mozilla/5.0" -o "$BATCH_DIR/news_{source}_{brand}_{detail}.jpg" "CDN_URL"
```

**Already in dataset:** ~78 news files. Check dedup by searching for the brand + location keywords.

---

## SLOT 4 — Manufacturer Websites + Wikipedia Brand Articles

### Part A — Signage Manufacturer Galleries

These Australian companies install fuel station signs and have portfolio galleries with professional photos:

| Site | URL | Notes |
|------|-----|-------|
| CV Media & Signage | cvmediasignage.com.au | OTR pylon photos |
| Signtronics | signtronics.com.au | Gold Coast manufacturer |

Fetch each gallery page → extract `<img>` URLs → download with browser User-Agent:
```bash
curl -sL -H "User-Agent: Mozilla/5.0" -o "$BATCH_DIR/mfr_{brand}_{detail}.jpg" "URL"
```

**Do NOT re-scrape these (already fully scraped):**
- Albert Smith Signs (albertsmithsigns.com.au) — 42 files in dataset
- Sydney LED Signs (sydneyledsigns.com.au) — 22 files in dataset

### Part B — Wikipedia Brand Articles

These Wikipedia articles often embed station photos with price signs. Fetch each article, find images in the HTML, download ones with visible price signs.

```
en.wikipedia.org/wiki/Metro_Petroleum
en.wikipedia.org/wiki/Costco#Australia
en.wikipedia.org/wiki/OTR_(convenience_store)
en.wikipedia.org/wiki/Puma_Energy
en.wikipedia.org/wiki/Liberty_Oil
en.wikipedia.org/wiki/Viva_Energy_Australia
en.wikipedia.org/wiki/EG_Group
en.wikipedia.org/wiki/Ampol
en.wikipedia.org/wiki/7-Eleven#Australia
en.wikipedia.org/wiki/Coles_Express
en.wikipedia.org/wiki/United_Petroleum
```

Extract image filenames from the article HTML, then download via the Wikimedia API:
```bash
curl -sL -o "$BATCH_DIR/wiki_article_{brand}_{detail}.jpg" \
  "https://api.wikimedia.org/core/v1/commons/file/File:FILENAME/download"
```

**Already in dataset:** ~55 wiki_article files. Only download NEW images not already present.

---

## SLOT 5 — Flickr + Wikimedia Price/Brand Categories

### Part A — Flickr "Great Aussie Petrol Station" Group

Group page: `flickr.com/groups/1256793@N23/`

This group has ~1,244 photos. **Most are heritage/vintage — be very selective.** Only save images that show modern stations with readable LED price signs. Skip heritage pumps, historical stations, and photos without price boards.

Flickr group pool browsing requires fetching the group page. Look for photo URLs in the page source.

Download Flickr photos at 1024px resolution:
```
https://live.staticflickr.com/SERVER/PHOTO_ID_SECRET_b.jpg
```

**Already in dataset:** ~51 flickr files. Many were correctly skipped as heritage.

### Part B — Wikimedia Price-Specific Categories

```
Category:Gasoline_price_boards                     (global — filter for Australian)
Category:Gasoline_price_displays                   (global — filter for Australian)
Category:Shell_petrol_stations_in_Australia         (~33 files)
Category:BP_petrol_stations_in_Australia            (~32 files)
Category:Caltex_petrol_stations_in_Australia        (~52 files)
Category:Ampol_petrol_stations                      (subcategories)
```

Browse via API (same pattern as Slot 1). For Gasoline_price_boards/displays, many images are international — only download Australian stations.

**Already in dataset:** ~54 gasboard files, ~29 Shell files, ~35 Ampol files, ~62 Caltex files. Dedup carefully.

---

## Dedup (MANDATORY — before EVERY download)

Before downloading ANY image, you MUST check if it already exists:

```bash
# Check by keyword (brand, location, source)
find data/ingest/ -type f -iname "*KEYWORD*" 2>/dev/null
ls data/tmp/ | grep -i "KEYWORD"

# For Wikimedia: check by the original filename fragment
find data/ingest/ -type f -iname "*WIKI_FILENAME_PART*" 2>/dev/null
ls data/tmp/ | grep -i "WIKI_FILENAME_PART"
```

Check **both** `data/ingest/` (new scrapes from all agents) and `data/tmp/` (existing dataset). If a similar file exists in either location, **skip it**.

## Where to Save

At the START of your session, create your batch directory:

```bash
BATCH_DIR="data/ingest/batch_$(date -u +%Y%m%dT%H%M%S)"
mkdir -p "$BATCH_DIR"
```

- Write ONLY to your `$BATCH_DIR`
- Keep it flat — no subdirectories inside
- Do NOT write to `data/ingest/` root
- Do NOT write to `data/tmp/`

## File Naming

```
{source}_{brand}_{location}_{detail}.{ext}

Sources: wiki, mfr, news, flickr, web

Examples:
  wiki_shell_leonora_wa_2018.jpg
  mfr_bp_caboolture_pylon.jpg
  news_sbs_narrabri_prices.jpg
  flickr_caltex_sydney_night.jpg
  wiki_article_metro_sydney.jpg
```

## Commit Pattern

After downloading a batch of images:

```bash
git add "$BATCH_DIR"/*.jpg "$BATCH_DIR"/*.png "$BATCH_DIR"/*.jpeg
git commit -m "scrape: add N images from SOURCE — BRANDS covered

batch: $BATCH_DIR
slot: SLOT_N"
```

Commit in batches of 10-30 images. **Do NOT `git push`** — the main agent reviews and pushes.

## Quality Bar

**Before saving each image, ask yourself:** "Can I see a fuel price sign with at least one readable fuel type label AND one readable price?" If no → don't save it.

## Sources That DON'T Work

Do not waste time on these — they have been tested and do not yield results:
- **Google Image Search** — no API, can't extract thumbnails
- **Dreamstime / stock photo sites** — 403 Forbidden on automated fetch
- **Pinterest** — requires authentication
- **Reddit** — no usable image results for fuel signs
- **eBay AU** — only Chinese LED module product listings
- **Flickr search page** — JavaScript-rendered, WebFetch gets empty HTML (use the group pool instead)
- **Direct news site crawling** — blocked by robots.txt (but CDN image URLs work — see Slot 3)
- **Pexels / Pixabay** — 403 on automated fetch
- **Geograph.org.au** — zero fuel sign results
