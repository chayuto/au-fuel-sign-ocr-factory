# Scrape Prompt: Australian Fuel Station Price Sign Images (v1)

## Agent Configuration

Launch scraping subagents with **Sonnet** (`model: "sonnet"`). Scraping is mechanical work (fetch pages, extract URLs, download, verify) and does not need Opus. Max **5-8 parallel scraper agents** to avoid API rate limits.

## Guardrails

Scrape agents are error-prone. These rules are non-negotiable:

1. **Write ONLY to your own batch directory** (see "Where to save" below) — never `data/tmp/`, never project root, never anywhere else
2. **Do NOT modify any existing files** — no editing manifests, logs, configs, scripts, or code
3. **Do NOT `git push`** — commit locally only, main agent reviews before push
4. **Do NOT run training, labeling, or build scripts** — scrape agents only download images
5. **Verify each download** — check file size > 1KB and file is a valid image before keeping
6. **Follow the naming convention exactly** — `{source}_{brand}_{location}_{detail}.{ext}`

## Scope

**This prompt is for IMAGE SCRAPING only.** Your job is to find and download images. Nothing else.

You do NOT:
- Label, annotate, or draw bounding boxes on images
- Edit manifests, logs, or CSV files
- Run Python scripts (except curl/wget for downloads)
- Modify anything in `data/tmp/` — that directory is off-limits
- Touch any code, configs, or docs

If you're unsure whether something is in scope, it isn't. Just download images.

## Current Dataset State (2026-03-30)

**Brand gaps — prioritize these when scraping:**

| Brand | Current images | Priority |
|-------|---------------:|----------|
| **Costco** | **0** | CRITICAL — zero images |
| **Metro** | **0** | CRITICAL — zero images |
| OTR | 2 | Very light |
| Liberty | 4 | Light |
| 7-Eleven | 9 | Need more |

**Scenario gaps:** Night/dusk, rain/overcast, angled views, rural/outback stations.

## Mission

Collect real-world images of **Australian fuel station price sign boards** — the pylon or wall-mounted signs that display fuel type labels and LED/printed prices. These images train a YOLO object detection model.

**You are collecting training data, not browsing.** Every image you save must contain a **visible fuel price sign with readable prices**. Station-only shots, pump closeups, brand logos without prices, historical photos without price boards — these are all waste. Be selective.

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
| Shell | HIGH | Red LED on dark panel. Often co-branded Coles Express |
| BP | HIGH | Green LED on green panel |
| Ampol | HIGH | White/red LED on dark blue panel |
| Caltex | HIGH | Rebranding to Ampol. White/red on red or white |
| 7-Eleven | HIGH | Red/orange LED. Co-branded Mobil |
| United | MEDIUM | Red LED on blue panel |
| Costco | HIGH | Rare — need more. Distinctive canopy-mounted |
| Liberty | MEDIUM | Red/amber LED on dark blue |
| Puma | MEDIUM | Red/amber on dark panel |
| OTR | MEDIUM | White LED on red panel. SA/VIC only |
| Metro | HIGH | Need more. Blue/red branding |
| Mobil | MEDIUM | Red LED on blue panel |
| Independent | LOW | Varies widely |

## Scenario Gaps (High Priority)

These are underrepresented in the current dataset — actively seek them:
- **Night/dusk shots** with illuminated LED signs
- **Rain/overcast** weather conditions
- **Angled/perspective** views (not perfectly frontal)
- **Rural/outback** station signs (regional pricing)
- **Multiple signs** in one frame (competing stations)
- **Costco** fuel stations (very few in dataset)
- **Metro Petroleum** (zero in dataset)

## Proven Source Strategies

Use these approaches in order of effectiveness:

### 1. Wikimedia Commons Category Browsing (Best yield)

Browse these categories and download images with visible price signs:

```
Category:Petrol_stations_in_Victoria,_Australia    (56 files)
Category:Petrol_stations_in_New_South_Wales        (62 files)
Category:Petrol_stations_in_Queensland             (53 files)
Category:Petrol_stations_in_Western_Australia      (28 files)
Category:Petrol_stations_in_South_Australia
Category:Shell_petrol_stations_in_Australia         (33 files)
Category:BP_petrol_stations_in_Australia            (32 files)
Category:Caltex_petrol_stations_in_Australia        (52 files)
Category:Ampol_petrol_stations                      (subcategories)
Category:United_Petroleum
Category:Puma_petrol_stations_in_Australia          (12 files)
Category:Gasoline_price_boards
Category:Gasoline_price_displays
```

**Download pattern:**
```bash
# Use Wikimedia REST API (most reliable):
curl -sL -o "output.jpg" \
  "https://api.wikimedia.org/core/v1/commons/file/File:FILENAME/download"

# Or use Special:FilePath with width limit:
curl -sL -o "output.jpg" \
  "https://commons.wikimedia.org/wiki/Special:FilePath/FILENAME?width=1024"
```

**Important:** The REST API (`api.wikimedia.org`) is more reliable than `Special:FilePath` which sometimes returns HTML error pages.

### 2. Signage Manufacturer Websites (Professional quality)

These AU companies install fuel station signs and have portfolio galleries:

| Site | URL | Notes |
|------|-----|-------|
| Albert Smith Signs | albertsmithsigns.com.au/industry/petroleum-signage/ | Best source. Needs User-Agent header. |
| Sydney LED Signs | sydneyledsigns.com.au/petrol-price-signs/ | LED digit product photos |
| CV Media & Signage | cvmediasignage.com.au | OTR pylon photos |
| Signtronics | signtronics.com.au | Gold Coast manufacturer |

**Download pattern:** Fetch page → extract `<img>` URLs → download with browser User-Agent:
```bash
curl -sL -H "User-Agent: Mozilla/5.0" -o "output.jpg" "URL"
```

### 3. News Article Image Extraction (Two-step)

Search for fuel price articles, then fetch the page to extract CDN image URLs:

**Step 1 — Search:**
```
"fuel price" OR "petrol price" station sign Australia 2024 2025 2026
```

**Step 2 — Fetch article, extract images:**
News sites block crawlers but their CDN images are accessible:
- ABC News: `live-production.wcms.abc-cdn.net.au`
- SBS: `sbs-au-brightspot.s3.ap-southeast-2.amazonaws.com`
- Carsales: `editorial.pxcrush.net`
- CarExpert: `images.carexpert.com.au`
- Yahoo News AU: accessible directly
- Regional newspapers (Bunbury Mail, etc.): `/images/transform/v1/crop/frm/`

### 4. Flickr Groups (Mixed quality)

The **"Great Aussie Petrol Station" group** (flickr.com/groups/1256793@N23/) has 1,244 photos. Most are heritage/vintage, but some show modern stations with price signs. Browse selectively.

Download Flickr photos at 1024px:
```
https://live.staticflickr.com/SERVER/PHOTO_ID_SECRET_b.jpg
```

### 5. Wikipedia Article Images

Articles for fuel brands often embed station photos:
- en.wikipedia.org/wiki/Ampol
- en.wikipedia.org/wiki/Coles_Express
- en.wikipedia.org/wiki/EG_Australia
- en.wikipedia.org/wiki/United_Petroleum
- en.wikipedia.org/wiki/Liberty_Oil

## Sources That DON'T Work

Do not waste time on these:
- **Google Image Search** — no API, can't extract thumbnails
- **Dreamstime / stock sites** — 403 Forbidden
- **Pinterest** — auth wall
- **Reddit** — no image results for fuel signs
- **eBay AU** — only Chinese LED module listings
- **Flickr search page** — JS-rendered, WebFetch gets empty HTML
- **Direct news site crawling** — blocked by robots.txt (but article CDN images work)
- **Pexels / Pixabay** — 403 on automated fetch
- **Geograph.org.au** — zero fuel sign results

## Output

### File naming

```
{source}_{brand}_{location}_{detail}.{ext}

Examples:
  wiki_shell_leonora_wa_2018.jpg
  mfr_bp_caboolture_pylon.jpg
  news_sbs_narrabri_prices.jpg
  flickr_caltex_sydney_night.jpg
```

### Where to save

Each agent creates its own batch directory under `data/ingest/` using the start timestamp:

```bash
# At the START of your session, set your batch dir:
BATCH_DIR="data/ingest/batch_$(date -u +%Y%m%dT%H%M%S)"
mkdir -p "$BATCH_DIR"
```

This produces directories like:
```
data/ingest/batch_20260330T120000/
data/ingest/batch_20260330T120015/
data/ingest/batch_20260330T120030/
```

Each agent writes ONLY to its own `$BATCH_DIR`. This prevents file collisions when multiple agents run in parallel — each agent owns its directory, no coordination needed.

**IMPORTANT:**
- Do NOT write to `data/tmp/` — that directory is off-limits to scrape agents
- Do NOT write to `data/ingest/` root — always use your `$BATCH_DIR`
- Do NOT write to another agent's batch directory
- Do NOT create subdirectories inside your `$BATCH_DIR` — keep it flat

### Commit pattern

After downloading a batch of images, commit only your own batch directory:

```bash
git add "$BATCH_DIR"/*.jpg "$BATCH_DIR"/*.png "$BATCH_DIR"/*.jpeg
git commit -m "scrape: add N images from SOURCE — BRANDS covered

batch: $BATCH_DIR"
```

Commit in batches of 10-30 images. Include source and brand coverage in the commit message. **Do NOT `git push`** — the main agent reviews and pushes.

### Dedup

Before downloading, check if a file with similar name already exists:
```bash
find data/ingest/ -name "*KEYWORD*" -type f 2>/dev/null
ls data/tmp/ | grep -i "KEYWORD"
```
Check **both** — `data/ingest/` including all batch subdirs (new scrapes) and `data/tmp/` (existing dataset). Do not download duplicates.

## Quality Bar

**Ask yourself before saving each image:** "Can I see a fuel price sign with at least one readable fuel label AND one readable price?" If no → don't save it.

Aim for quantity with quality: **50+ usable images per scrape session**, covering at least 3 different brands and 2 different sources.
