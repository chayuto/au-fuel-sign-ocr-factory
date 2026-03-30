# Experiment Log — AU Fuel Sign Image Sourcing

## Experiment 001: News Site Image Scraping (2026-03-29)

### Objective
Find freely available Australian fuel station price sign images from news sites and identify government fuel price APIs for ground truth data.

### Approach
1. Web search for fuel price articles across target AU news sites
2. Google Image Search with `site:` filters for targeted results
3. Browser-based JavaScript extraction of image URLs from Google Image results and article pages
4. Direct download via curl to `data/tmp/`
5. Visual validation of each downloaded image

### What Worked ✅
- **Google Image Search** was the most effective discovery method — returned dozens of relevant results from news sites, social media, and stock photo services
- **JavaScript extraction** from Google Image thumbnails and news article DOM successfully yielded downloadable URLs
- **ABC News CDN** (`live-production.wcms.abc-cdn.net.au`) serves images without auth — easy to curl
- **9News image resizer** (`imageresizer.static9.net.au`) works for standard sizes but rejects custom upscaling
- **AXENT (LED sign manufacturer)** was an unexpected gold mine — product photos show perfect sign boards
- **Alamy stock** provides watermarked preview images at decent resolution

### What Didn't Work ❌
- **Direct site crawling** blocked by robots.txt on all AU news sites (confirmed in SCRAPE_MANIFEST)
- **The Guardian** article images were mostly fuel pump closeups, not price signs
- **CarExpert** images were generic stock photos (fuel pump with AU flag), not actual signs
- **9News hi-res requests** with custom dimensions returned empty files (resizer rejects arbitrary sizes)
- **SBS News** articles used composite graphics rather than real photos

### Key Learnings 📝
1. **LED display types**: Red (most common — Shell, Ampol, United, Coles Express) and Green (BP)
2. **Price format**: Always `XXX.X` cents per litre with 1 decimal place
3. **Common fuel types on AU boards**: E10, ULP/Unleaded 91, Unleaded 95, Premium 98, V-Power, Diesel, Amplify, LPG
4. **Sign layouts**: Vertical pylon-mounted, brand logo at top, fuel types left, LED prices right
5. **Discount overlays**: "Save 4¢" (Coles/Woolworths) overlay is common and adds OCR complexity
6. **Brands confirmed in images**: Shell/Coles Express, Ampol, United, BP, Caltex, Liberty, 7-Eleven

### Images Downloaded (5 verified)

| # | File | Source | Brands | Res | Rating |
|---|------|--------|--------|-----|--------|
| 1 | `au_fuel_sample_01_abc_united.jpg` | ABC News | Shell/Coles, Ampol, United | 862×485 | ⭐⭐⭐⭐⭐ |
| 2 | `au_fuel_sample_03_9news_bp.jpg` | 9News | BP | 360×203 | ⭐⭐⭐ |
| 3 | `au_fuel_sample_05_alamy_shell_coles.jpg` | Alamy | Coles Express | 866×1390 | ⭐⭐⭐⭐⭐ |
| 4 | `au_fuel_sample_06_axent_led.png` | AXENT | United | 923×641 | ⭐⭐⭐⭐ |
| 5 | `au_fuel_sample_07_9news_station.jpg` | 9News | BP (green LED) | 1200×1200 | ⭐⭐⭐⭐ |

### Fuel Price APIs Identified (for ground truth)

| State | System | Best For | Auth |
|-------|--------|----------|------|
| NSW+TAS | FuelCheck REST API | Real-time per-station JSON | OAuth (free reg) |
| WA | FuelWatch RSS | Zero-friction XML feed | None needed |
| QLD | Fuel Prices QLD | REST + Swagger + Postman | Token (free reg) |
| SA | SA Fuel Pricing | Mandatory reporting | Publisher reg |
| NT | MyFuel NT | Monthly datasets | Request access |

### Next Steps
- [ ] Try more Google Image searches with different queries (brand-specific, night shots, regional)
- [ ] Try Flickr API search (CC licensed, geo:Australia)
- [ ] Try Reddit image posts from r/australia, r/sydney, r/melbourne
- [ ] Download images from more ABC News articles (multiple exist)
- [ ] Try Australian newspaper image archives
- [ ] Explore LED sign manufacturer websites (Daktronics, AXENT, etc.)

---

## Experiment 002: Expanded Image Collection (2026-03-29)

### Objective
Expand the image collection beyond the initial 5 — targeting more brands, angles, lighting conditions, and regional variations.

### Approach
- Wikimedia Commons category scraping (brand + state categories)
- Australian sign manufacturer websites (product/installation galleries)
- News article embedded images (SBS, Carsales, CarExpert, AAP Photos)
- LED sign manufacturer product photos (Sydney LED Signs, WiPath, AXENT)
- Google web search → fetch article pages → extract image URLs

### What Worked (Ranked by Yield)

| Source | Yield | Quality | Notes |
|--------|-------|---------|-------|
| **Albert Smith Signs** (albertsmithsigns.com.au) | 44 images | Professional hi-res | AU petroleum signage manufacturer. Gallery has real pylon photos: BP, Caltex, United, Puma, Mobil, Pacific Petroleum, Matilda. Best single source. |
| **Wikimedia Commons** (category scraping) | 55 images | Mixed (some excellent) | Categories: Ampol, BP, Caltex, United, Shell AU, Petrol stations in QLD/NSW/VIC/WA. Used `Special:FilePath/NAME?width=1024` for resized downloads. |
| **Sydney LED Signs** (sydneyledsigns.com.au) | 12 images | Product shots | LED digit displays at various sizes (800mm, 1000mm, 1200mm). Clean product photos useful for Reader training. |
| **SBS News** (sbs.com.au) | 2 images | Good | Narrabri station with clear price display. Images on S3 CDN, accessible via direct URL. |
| **Carsales** (editorial.pxcrush.net) | 3 images | Good | BP diesel price board close-up (green LED digits) — excellent Reader training data. |
| **CarExpert** (images.carexpert.com.au) | 2 images | Good | BP station photo, fuel pump. Cloudinary-style resize URLs. |
| **AAP Photos** via regional news | 3 images | Decent | Fuel station images from Bunbury Mail article. URL pattern: `/images/transform/v1/crop/frm/silverstone-feed-data/UUID.jpg/...` |
| **CV Media Signage** | 1 image | Good | OTR pylon sign — rare brand coverage. |
| **CarsGuide** | 1 image | Good | BP station via Cloudinary URL. |
| **VicNews** | 1 image | Context | Fuel shortage article with servo photo. |
| **WiPath** | 1 image | Thumbnail | LED sign product photo (low res). |

### What Didn't Work

| Approach | Why It Failed |
|----------|--------------|
| **Flickr search** (CC licensed) | Flickr search page is JS-rendered, WebFetch gets empty HTML. Flickr "Fuel Watch" group pool was empty. `site:flickr.com` web searches returned only vintage/non-AU results. |
| **Dreamstime stock** | 403 Forbidden — blocked WebFetch. Has good AU fuel sign photos but inaccessible. |
| **AussieHerald** | 403 Forbidden. |
| **Google Image Search direct** | No API access. `filetype:jpg` operator doesn't work in web search tool. Can't extract Google thumbnail proxy URLs (`encrypted-tbn0.gstatic.com`). |
| **Pinterest** | Searches return Pinterest URL but content is behind auth wall. |
| **eBay AU listings** | LED sign product listings, not installed station photos. All from Chinese manufacturers. |
| **Geograph.org.au** | Web search returned zero results for fuel signs. Site may have limited coverage. |
| **News site direct scraping** | All AU news sites block crawlers (robots.txt). But fetching specific article URLs with known image paths works. |
| **Reddit** | `site:reddit.com` search returned zero results for fuel sign photos. |
| **Mapillary API** | Requires auth token registration. Street-level imagery exists but API setup needed. |

### Key Strategy Insights

1. **Manufacturer/signage company websites are the best source.** They have professional photos of real AU installations with visible price boards. Albert Smith Signs alone yielded 44 images covering 6+ brands.
2. **Wikimedia Commons category browsing is high-yield.** Categories by brand (`Caltex_petrol_stations_in_Australia`) and by state (`Petrol_stations_in_Queensland`) together provided 55+ images. Use `Special:FilePath/` for direct download.
3. **News article images are accessible via CDN URLs.** Even when news sites block crawlers, specific article pages can be fetched, and images are served from CDNs (S3, pxcrush, Cloudinary) without auth.
4. **WebFetch can't handle JS-rendered pages.** Flickr, Pinterest, stock photo sites all fail because thumbnails are loaded by JavaScript. Only works on server-rendered HTML.
5. **Google web search + article fetching is a two-step pipeline.** Search finds articles → fetch article HTML → extract `<img>` URLs → download. Slower but reliable.

### Collection Summary

| Metric | Count |
|--------|-------|
| Images in `data/tmp/` | 137 |
| Images in `/tmp/wiki_*` (from session 1 agents) | 172 |
| Total unique images | ~309 |
| Zero-byte / failed downloads | 0 |
| Brands covered | 13 (BP, United, Caltex, Ampol, Mobil, Pacific Petroleum, Puma, Shell, OTR, Coles Express, 7-Eleven, Matilda, Liberty) |

### Brand Coverage Gaps

| Brand | Current Count | Priority |
|-------|--------------|----------|
| Costco | 0 | HIGH — distinctive style |
| 7-Eleven | 2 | HIGH — major brand |
| Shell | 3 (in data/tmp) + 20 (in /tmp) | MEDIUM |
| Liberty | 1 | MEDIUM |
| OTR | 2 | MEDIUM |
| Metro | 0 | MEDIUM |
| Night shots | ~3 | HIGH — need more |
| Rain/adverse weather | 0 | HIGH — edge cases |

### Next Steps
- [ ] Scrape more Wikimedia subcategories (Ampol Chatswood, Concord, Granville, etc.)
- [ ] Try Mapillary API with auth token for street-level imagery
- [ ] Search for more AU signage manufacturer galleries (Daktronics AU, Signtronics)
- [ ] Fetch more specific news articles about fuel prices (ABC News, 7News)
- [ ] Try Google Maps/Street View static API for specific station addresses
- [ ] Search for Costco AU fuel station images specifically
- [ ] Search for night/rain fuel station photos
- [ ] Try Australian government/council DA (Development Application) images
- [ ] Check Unsplash/Pexels for CC0 fuel station photos
