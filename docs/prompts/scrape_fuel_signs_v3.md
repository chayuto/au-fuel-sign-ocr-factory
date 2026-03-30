# Scrape Prompt: Australian Fuel Station Price Sign Images (v3 — New Sources)

## Your Mission

You are a scraping agent. Your job is to find and download real-world images of **Australian fuel station price sign boards** from **sources not previously scraped**. These images train a YOLO object detection model.

**v2 has exhausted:** Wikimedia Commons categories, Wikipedia brand articles, Flickr "Great Aussie Petrol Station" group, Albert Smith Signs, Sydney LED Signs, and most Australian news CDNs. This prompt targets **fresh sources** to fill critical brand and scenario gaps.

## Critical Gaps (Priority Order)

| Gap | Current Count | Target | Why |
|-----|--------|--------|-----|
| **Costco** | **0** | 10+ | Distinctive canopy-mounted signs. Rare but growing. |
| **Metro Petroleum** | **1** | 10+ | Blue/red branding. ~160 stations nationwide. |
| **OTR** | **2** | 10+ | SA/VIC only. Red panel, white LED. |
| **Liberty** | **4** | 10+ | Dark blue panel. ~50 stations. |
| **Night/dusk** | ~15% | 30%+ | Illuminated LED signs look different at night |
| **Rain/overcast** | ~10% | 20%+ | Reflections and glare affect detection |
| **7-Eleven** | **7** | 15+ | Red/orange LED. Co-branded Mobil. |
| **Rural/outback** | sparse | more | Regional pricing, different sign styles |

## Scope & Guardrails

Same rules as v2 — this is IMAGE SCRAPING only:

1. **Write ONLY to your batch directory** (see "Where to save" below)
2. **Do NOT modify any existing files** — no manifests, logs, configs, scripts, code
3. **Do NOT `git push`** — commit locally, main agent reviews before push
4. **Do NOT run training, labeling, or build scripts**
5. **Do NOT write to `data/tmp/`** — off-limits
6. **Verify each download** — file size > 1KB, valid image format
7. **Follow naming convention** — `{source}_{brand}_{location}_{detail}.{ext}`
8. **Dedup before every download** (see Dedup section)

## What Makes a GOOD Image

A good image has ALL of these:
- A fuel price **sign board** is visible (pylon, canopy fascia, or wall panel)
- At least one **fuel type label** is readable (e.g., "Unleaded", "Diesel", "E10")
- At least one **price** is readable (LED digits or printed numbers, format: XXX.X cents/litre)
- The sign is large enough in frame (~>10% of image area)

---

## SLOT 1 — Mapillary (Open Street-Level Imagery)

Mapillary has millions of crowdsourced street-level photos across Australia. Many capture fuel station signage while driving past.

**API approach:**
```bash
# Search for images near known fuel station coordinates
# Mapillary API v4 (free, needs access token)
# Get images within 50m of a fuel station location
curl -s "https://graph.mapillary.com/images?access_token=TOKEN&fields=id,thumb_1024_url,geometry&bbox=LON1,LAT1,LON2,LAT2&limit=100"
```

**Strategy:**
1. Use known Costco/Metro/OTR station addresses (see Target Locations below)
2. Query Mapillary for images within 50-100m radius
3. Download thumbnails at 1024px
4. Visually verify — most street-level images won't show readable prices, but some capture signs clearly

**Target Locations (Costco):**
- Costco Docklands VIC: -37.8152, 144.9472
- Costco Moorabbin VIC: -37.9369, 145.0515
- Costco Epping VIC: -37.6503, 145.0167
- Costco Marsden Park NSW: -33.7222, 150.8347
- Costco Auburn NSW: -33.8472, 151.0347
- Costco Casula NSW: -33.9528, 150.9083
- Costco North Lakes QLD: -27.2250, 152.9833
- Costco Bundamba QLD: -27.6136, 152.8028
- Costco Perth Airport WA: -31.9403, 115.9689
- Costco Canberra ACT: -35.2019, 149.1422

**Target Locations (Metro Petroleum):**
- Metro Bankstown NSW: -33.9167, 151.0333
- Metro Merrylands NSW: -33.8333, 150.9833
- Metro Fairfield NSW: -33.8667, 150.9500
- Metro Cabramatta NSW: -33.8833, 150.9333
- Metro Greenacre NSW: -33.9000, 151.0500

**Download pattern:**
```bash
curl -sL -o "$BATCH_DIR/mapillary_{brand}_{location}.jpg" "THUMB_URL"
```

**Already in dataset:** 0 Mapillary images. This is a completely new source.

---

## SLOT 2 — FuelWatch WA & NSW FuelCheck

Australian state governments run fuel price comparison websites. Some pages embed station photos.

### FuelWatch (Western Australia)
Website: `fuelwatch.wa.gov.au`

```
Search for stations, fetch result pages, extract any embedded images.
Focus on rural WA stations (underrepresented) and Liberty/independent brands.
```

### NSW FuelCheck
Website: `fuelcheck.nsw.gov.au`

```
Search by brand (Metro, Liberty), fetch station detail pages.
Some stations have user-uploaded or Google Street View thumbnails.
```

### QLD Fair Trading Fuel Prices
Website: `fuelprice.qld.gov.au` or `data.qld.gov.au`

```
QLD government fuel data portal. Check for any embedded imagery.
```

**Download pattern:**
```bash
curl -sL -H "User-Agent: Mozilla/5.0" -o "$BATCH_DIR/govau_{brand}_{location}.jpg" "URL"
```

---

## SLOT 3 — Google Maps Place Photos API

Google Places API returns user-uploaded photos for businesses. Fuel stations often have photos showing their price signs.

**Requires:** Google Cloud API key with Places API enabled.

**Strategy:**
1. Search for target brand stations by name + location
2. Get place_id from search results
3. Fetch place photos (up to 10 per place)
4. Download at max resolution

```bash
# Step 1: Find place
curl -s "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=Costco+fuel+Docklands+Melbourne&inputtype=textquery&fields=place_id,photos&key=API_KEY"

# Step 2: Get photo reference from response, then download
curl -sL -o "$BATCH_DIR/gmaps_{brand}_{location}.jpg" \
  "https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photo_reference=PHOTO_REF&key=API_KEY"
```

**Priority targets:**
- All 10 Costco fuel locations (see Slot 1 coordinates)
- Metro Petroleum stations in Sydney
- OTR stations in Adelaide
- Liberty stations

**Already in dataset:** 0 Google Maps photos.

---

## SLOT 4 — Fuel Brand Social Media (Public Pages)

Australian fuel brands and station operators post station photos on public Facebook/Instagram pages. These often show price signs prominently.

**Facebook Pages to check:**
```
Costco Australia (official)
Metro Petroleum (official)
OTR (On The Run) (official)
Liberty Oil Australia (official)
7-Eleven Australia (official)
United Petroleum (official)
```

**Strategy:**
1. Fetch the public Facebook page
2. Look for photo posts showing station exteriors with price signs
3. Extract image CDN URLs from page source
4. Download at highest available resolution

**Instagram accounts:**
```
@costco_au (check for fuel station posts)
@metropetroleum
@oikigroup (OTR parent)
@libertyoil_au
```

**Download pattern:**
```bash
curl -sL -H "User-Agent: Mozilla/5.0" -o "$BATCH_DIR/social_{brand}_{location}_{detail}.jpg" "CDN_URL"
```

**Note:** Only download from PUBLIC pages. Do not attempt to bypass login walls.

---

## SLOT 5 — Australian Automotive & Local News

### Automotive Forums & Blogs
```
whirlpool.net.au "fuel price" sign photo
ozbargain.com.au fuel price servo
carsguide.com.au fuel price sign
drive.com.au petrol price sign
caradvice.com.au fuel price board
```

Fetch search result pages, find articles with embedded images, download those showing price signs.

### Regional/Local News (untapped in v2)
```
"fuel price" site:theaustralian.com.au
"petrol price" site:smh.com.au
"fuel price sign" site:perthnow.com.au
"petrol price" site:adelaidenow.com.au
"fuel price" site:couriermail.com.au
"petrol prices" site:thewest.com.au
"fuel price" site:canberratimes.com.au
"petrol price" Costco Australia
"Metro Petroleum" fuel price sign
"OTR fuel" price sign Adelaide
"Liberty fuel" price sign Australia
```

**CDN domains likely to work:**
- News Corp: `content.api.news`, `cdn.newsapi.com.au`
- Nine/Fairfax: `static.ffx.io`, `images.nine.com.au`
- Seven West: `images.perthnow.com.au`, `thewest.com.au/image`
- Canberra Times: `images.canberratimes.com.au`

### YouTube Thumbnails
Search for Australian fuel price videos — thumbnails often show price signs clearly.
```
# YouTube search → get video IDs → fetch max-res thumbnails
# Thumbnail URL pattern:
https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg
# Fallback if maxres doesn't exist:
https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg
```

Search queries for YouTube:
```
"Australian fuel prices" 2025
"petrol prices Australia" sign
"Costco fuel" Australia
"OTR fuel prices" Adelaide
"servo prices" Melbourne
```

**Download pattern:**
```bash
curl -sL -o "$BATCH_DIR/ytthumb_{brand}_{detail}.jpg" "https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg"
```

---

## SLOT 6 — Signage Industry & Commercial Real Estate

### Signage Manufacturers (not yet scraped)

| Company | URL | Notes |
|---------|-----|-------|
| Daktronics AU | daktronics.com/en-au | US manufacturer with AU installations |
| Vantage LED | vantageled.com.au | LED sign manufacturer |
| Mega Signs | megasigns.com.au | Perth-based, fuel signage |
| LED Craft | ledcraft.com.au | LED price displays |
| Caltex/Ampol signage | Search for "Ampol rebranding signage" | Rebranding photos |

**Do NOT re-scrape these (already fully scraped):**
- Albert Smith Signs (42 files)
- Sydney LED Signs (22 files)
- CV Media & Signage (checked in v2)
- Signtronics (checked in v2)

### Commercial Real Estate Listings
Fuel stations being sold often have clear exterior photos with price signs.

```
# Search commercial real estate sites
"fuel station" OR "service station" site:commercialrealestate.com.au
"petrol station for sale" site:realcommercial.com.au
"service station" site:business2sell.com.au
```

---

## Dedup (MANDATORY — before EVERY download)

Before downloading ANY image, check both the existing dataset AND the perceptual hash index:

```bash
# Check by keyword (brand, location, source)
find data/ingest/ -type f -iname "*KEYWORD*" 2>/dev/null
find data/tmp/ -type f -iname "*KEYWORD*" 2>/dev/null

# For Wikimedia: check by the original filename fragment
find data/tmp/ -type f -iname "*WIKI_FILENAME_PART*" 2>/dev/null
```

Check **both** `data/ingest/` and `data/tmp/`. If a similar file exists, **skip it**.

**After your batch is complete**, the main agent will run the pipeline script which performs
3-level dedup (filename, SHA-256 hash, perceptual hash) to catch any duplicates you missed.

## Where to Save

```bash
BATCH_DIR="data/ingest/batch_$(date -u +%Y%m%dT%H%M%S)"
mkdir -p "$BATCH_DIR"
```

Write ONLY to your `$BATCH_DIR`. Keep it flat — no subdirectories.

## File Naming

```
{source}_{brand}_{location}_{detail}.{ext}

Sources: mapillary, gmaps, govau, social, ytthumb, forum, realestate, mfr, news, web

Examples:
  mapillary_costco_docklands_vic_2024.jpg
  gmaps_metro_bankstown_nsw_01.jpg
  govau_liberty_karratha_wa.jpg
  social_otr_adelaide_facebook.jpg
  ytthumb_costco_epping_vic.jpg
  forum_whirlpool_shell_night.jpg
  realestate_bp_rural_nsw.jpg
```

## Commit Pattern

```bash
git add "$BATCH_DIR"/*.jpg "$BATCH_DIR"/*.png "$BATCH_DIR"/*.jpeg
git commit -m "scrape: add N images from SOURCE — BRANDS covered

batch: $BATCH_DIR
slot: SLOT_N"
```

Commit in batches of 10-30 images. **Do NOT `git push`**.

## Sources That DON'T Work

Tested in v1/v2 — don't waste time:
- **Google Image Search** — no API, can't extract thumbnails
- **Dreamstime / stock photo sites** — 403 Forbidden
- **Pinterest** — requires authentication
- **Reddit** — no usable results
- **eBay AU** — Chinese LED modules only
- **Flickr search page** — JS-rendered, empty HTML
- **Pexels / Pixabay** — 403
- **Geograph.org.au** — zero results

## Quality Bar

**Before saving each image:** "Can I see a fuel price sign with at least one readable fuel type label AND one readable price?" If no → don't save it.

Prioritize Costco, Metro, OTR, Liberty, and night/rain scenarios above all else.
