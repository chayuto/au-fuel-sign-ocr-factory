# Scrape Prompt: Australian Fuel Station Price Sign Images (v5 — Quality Over Quantity)

## Your Mission

You are a scraping agent. Find and download real-world **photographs** of Australian fuel station price sign boards. These train a YOLO object detection model.

**Why v5?** v4 scraped 111 images but only 6 survived screening+labeling as usable training data (5.4% yield). The main failure modes were: news composites (sign pasted next to unrelated content), YouTube thumbnails without signs, pump displays mistaken for signs, and stylized/filtered photos. v5 has strict image quality rules to prevent wasting downstream labeling effort.

## Image Quality Rules (MANDATORY)

### ACCEPT only if ALL true:
1. **Natural camera photograph** — a single, unedited photo taken by a camera at a fuel station
2. **Fuel price sign board visible** — pylon sign, canopy fascia, or wall-mounted price panel
3. **At least one fuel type label readable** — "Unleaded", "Diesel", "E10", etc.
4. **At least one price readable** — LED or printed digits, XXX.X format (e.g., 189.9)
5. **Sign occupies ≥15% of image area** — close enough to annotate bounding boxes

### REJECT if ANY true:
- **News composite / editorial image** — sign stitched next to unrelated content (explosion, portrait, map, pump nozzle collage). If the image contains 2+ distinct photos joined together, REJECT.
- **Pump transaction display** — a pump LCD showing litres dispensed, dollar total, or per-litre price during a fill. This is NOT a price sign board.
- **Extreme close-up crop** — only the LED digits visible, no sign frame or station context. Real camera frames always include surrounding context.
- **Screenshot of app, website, or article** — not a direct photo
- **Stylized / filtered photo** — polaroid borders, Instagram filters, heavy post-processing, date stamps, large text overlays
- **Product catalog / manufacturer page** — sign shown alongside product specs or marketing copy
- **Sign too small** — less than 15% of image area (too distant or wide-angle)
- **Prices blank/off** — LEDs not illuminated, or placeholder 999.9 / 000.0
- **>70% occluded** by trees, poles, vehicles
- **Heritage/historical** — pre-1990s station with no modern price board

**When in doubt, REJECT.** 10 clean images beat 100 noisy ones for training.

## Current Dataset Gaps (Updated from v4)

| Brand | Have | Need | Priority |
|-------|------|------|----------|
| **Costco** | **0** | 10+ | CRITICAL — zero on Wikimedia, zero from YouTube. Need news/blog sources |
| **Metro** | **2** | 10+ | CRITICAL — zero on Wikimedia. Need news/blog sources |
| **OTR** | **~7** | 10+ | HIGH — v5 Wikimedia run added ~5 new OTR |
| **Liberty** | **~7** | 10+ | HIGH |
| **7-Eleven** | **7** | 15+ | MEDIUM |
| Night/dusk shots | ~15% | 30%+ | HIGH — LED signs look different at night |

**Well-represented (don't prioritize):** Caltex (43+), BP (25+), Shell (20+), Mobil (20+), Independent (18+), Ampol (17+), United (16+), Puma (13+)

## Source Strategy (Learned from v1-v5)

### BEST SOURCES (use these)
| Source | Effective Hit Rate | Notes |
|--------|-------------------|-------|
| **Wikimedia Commons** | ~10% after dedup | Best volume but mostly exhausted for common brands. Still useful for gap brands and state categories not yet crawled. |
| **News articles (direct photos only)** | ~10% after filtering composites | Only save the actual station photo, NOT the article composite. Best source for Costco/Metro since they have zero Wikimedia presence. |
| **YouTube thumbnails** | ~5% after filtering | Most are talking heads / memes. Only save if sign clearly visible. |

### KEY FINDING FROM v5
**Costco and Metro have ZERO images on Wikimedia Commons.** These brands must be sourced from news articles, YouTube, or direct web searches. Do not waste time on Wikimedia for these two brands.

**Wikimedia is heavily duplicated** — v5 scraped 97 images but only 9 were new after dedup. Focus Wikimedia scrapes on uncrawled state categories or specific gap brands.

### ZERO YIELD (do NOT attempt)
Mapillary, social media (FB/Insta), real estate, Flickr heritage, Google Images, stock photos, Pinterest, Reddit, Google Maps (no API key), signage manufacturer websites (v4: 0/8 usable), brand corporate sites (v4: 0/13 usable), fuel comparison apps (v4: 0/0 usable), forums (v4: 0/10 passed labeling)

## Download & Validation

```bash
BATCH_DIR="data/ingest/batch_$(date -u +%Y%m%dT%H%M%S)"
mkdir -p "$BATCH_DIR"
```

For EACH downloaded file, verify:
```bash
# Must be a real image (not HTML/JSON error page)
file "$BATCH_DIR/$name" | grep -qi "image"
# Must be >10KB (tiny files are placeholders/icons)
[ $(stat -f%z "$BATCH_DIR/$name") -gt 10240 ]
```

**IMPORTANT: After downloading, OPEN and LOOK at each image.** Apply the quality rules above. Delete anything that fails. Do NOT rely on filename or URL to judge content.

## Dedup (MANDATORY before every download)

```bash
find data/ingest/ -type f -iname "*KEYWORD*" 2>/dev/null
find data/tmp/ -type f -iname "*KEYWORD*" 2>/dev/null
```

Check BOTH paths. If similar file exists, skip.

## File Naming

```
{source}_{brand}_{location}_{detail}.{ext}

Sources: wiki, ytthumb, news, web
Brands: shell, bp, ampol, caltex, seven_eleven, united, costco, liberty, puma, metro, mobil, otr, independent

Examples:
  wiki_otr_adelaide_sa_01.jpg
  wiki_costco_epping_vic_01.jpg
  news_9news_metro_sydney_01.jpg
```

## Where to Save

Write ONLY to your `$BATCH_DIR`. Keep flat — no subdirectories.
Do NOT modify code, configs, manifests, `data/tmp/`, or anything outside the batch dir.
Do NOT `git push`.

## Scrape Report (MANDATORY)

Write `scrape_report.md` in your batch directory:

```markdown
# Scrape Report: v5 — [Source/Focus]

## Summary
- **Images saved:** N
- **Images rejected:** N (with reasons)
- **Brands covered:** list

## Quality Self-Check
For each saved image, confirm:
- [ ] Natural camera photo (not composite/screenshot/crop)
- [ ] Sign board visible with readable fuel type + price
- [ ] Sign ≥15% of image area
- [ ] Not a pump display, product catalog, or filtered photo

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| ... | ... | N | ... |
```

## Slot: Wikimedia Deep Scrape

This is a single focused slot. Crawl ALL Australian fuel station Wikimedia categories systematically:

### Categories (crawl all, skip already-scraped files via dedup)
```
Category:Petrol_stations_in_Australia (and all state subcategories)
Category:Fuel_prices_in_Australia
Category:On_The_Run_(convenience_stores)
Category:7-Eleven_in_Australia
Category:Puma_Energy
Category:Liberty_Oil
Category:Costco_Australia
Category:Metro_Petroleum
```

### Search queries (Wikimedia API)
```
"Costco fuel" Australia
"OTR fuel" OR "On The Run fuel"
"Metro Petroleum" price
"Liberty fuel" OR "Liberty Oil" Australia
"fuel price" sign Australia night
"petrol station" price board Australia
```

### API pattern
```bash
# Search
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=QUERY&srnamespace=6&format=json"

# Get download URL
curl -s "https://commons.wikimedia.org/w/api.php?action=query&titles=File:FILENAME&prop=imageinfo&iiprop=url&format=json"
```

**After downloading each image, READ it and apply the quality rules. Delete rejects immediately.**
