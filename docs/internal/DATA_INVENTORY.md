# Data Inventory — AU Fuel Sign OCR Factory

**Last updated:** 2026-03-29

## Source Search Results

### Existing Datasets (External)

| # | Dataset | Images | Classes | License | Relevance | Status |
|---|---------|--------|---------|---------|-----------|--------|
| 1 | Wikimedia "Gasoline price boards/displays" | ~333 (4 AU) | None (raw photos) | CC BY-SA 4.0 | **HIGH** — best free source | Seed set downloaded |
| 2 | Roboflow "Gas_Station" (Stela) | 6,754 | 1 (pylon sign) | CC BY 4.0 | MEDIUM — Brazilian signs, finder only | Not downloaded |
| 3 | Roboflow "Petrol tags detection" | 118 | 11 (Polish brands) | CC BY 4.0 | LOW — Polish, wrong brands | Not downloaded |
| 4 | Roboflow 7-segment digit datasets | ~8,100 combined | digits 0-9 | Various CC | MEDIUM — reader auxiliary | Not downloaded |
| 5 | Roboflow "LED Digital 1" | 2,360 | digits | CC BY 4.0 | MEDIUM — reader auxiliary | Not downloaded |

**Key finding: No existing annotated dataset of Australian fuel price signs exists.** Dataset must be built from scratch.

### Academic Prior Art

- **PetrolWatch (UNSW, 2008-2011)** — Australian fuel sign OCR from moving vehicles. 92.3% board detection, 87.7% price reading on 52 test images. **Dataset NOT publicly available.** Papers: DCOSS 2008, IEEE 2011.

### Kaggle / Open Images

- **Kaggle**: Only tabular CSV price data (no images)
- **Google Open Images V7**: No fuel/petrol/gas station classes in 600-class taxonomy

---

## Collected Images (Seed Set)

### Wikimedia Commons — Australian Fuel Signs

| File | Brand | Fuel Types | Prices (c/L) | Sign Type | State | License | Quality |
|------|-------|-----------|---------------|-----------|-------|---------|---------|
| `shell_leonora.jpg` | Shell/Coles Express | Unleaded, Diesel | 179.9, 176.9 | Backlit static | WA | CC BY-SA 4.0 | A |
| `shell_tolland.jpg` | Shell | 3 types | ~249.9, ~269.9, ~299.9 | LED red digits | NSW | CC BY-SA 3.0 AU | A |
| `mobil_albury.jpg` | Mobil | E10, Unleaded, Supreme 98, Diesel | 176.9, 178.9, 198.9, 188.9 | Blue LED | NSW | CC BY-SA 4.0 | A (best) |
| `caltex_woolworths.jpg` | Caltex/Woolworths | Unleaded + others | ~85.9, ~139.5, ~89.9 | LED pylon | AU | CC BY-SA 4.0 | B |
| `eg_ampol_sunshine.jpg` | Ampol/EG | Unleaded, Amplify 91, Diesel, LPG | 174.9, 187.9, 225.9, 89.9 | LED dark board | VIC | CC BY-SA 4.0 | A |
| `ampol_apollo_bay.jpg` | Ampol | 3 types | ~203, ~217, ~232 | Pylon red | VIC | CC BY-SA 4.0 | B |
| `united_brisbane.jpg` | United | E10, ULP, Diesel | 83.9, 87.9, 121.9 | LED red digits | QLD | CC BY-SA 4.0 | A |
| `mundrabilla.jpg` | Independent | ULP, Premium Diesel | 161.0, 161.0 | Mechanical flip | WA | CC BY-SA 4.0 | A |
| `bp_sydney.jpg` | BP/Wild Bean | Unleaded, Ultimate, Diesel, Autogas | 87.9, 123.9, 79.9, 110.9 | LED pylon | NSW | CC BY-SA 4.0 | A |

**Total: 9 images, 6 with clear price boards (Grade A-B)**
**Brands covered: Shell, Mobil, Caltex, Ampol/EG, United, BP, Independent**
**Sign types: LED (red), LED (blue), backlit, mechanical flip, pylon**

Files downloaded to `/tmp/au_fuel_sign_*.jpg` and `/tmp/news_fuel_*.jpg`.

### Additional Wikimedia Categories to Mine

- `Category:Petrol_stations_in_Victoria,_Australia` (57 files)
- `Category:Shell_petrol_stations_in_Australia` (33 files)
- `Category:Caltex_petrol_stations_in_Australia`
- `Category:Ampol_petrol_stations_in_Australia`

---

## Ground Truth APIs

| API | State | Auth | Format | Real-time | Historical | Notes |
|-----|-------|------|--------|-----------|-----------|-------|
| **FuelWatch RSS** | WA | None | XML/RSS | Yes | Since 2001 | Simplest, no auth |
| **FuelCheck API** | NSW+TAS | Free API key | REST JSON | Yes | Yes | 2,500 calls/month |
| **QLD Fuel Reporting** | QLD | CSV/registration | CSV | Yes | Since 2019 | By station + coordinates |
| **Servo Saver** | VIC | Application | API | 24hr delay | Yes | Email to request access |
| **SA Fuel Pricing** | SA | Via publishers | N/A | N/A | N/A | No direct public API |

---

## Auxiliary Datasets (Reader Training)

| Dataset | Images | Use Case | Notes |
|---------|--------|----------|-------|
| 7-segment digit datasets (Roboflow, 4 datasets) | ~8,100 | Price digit reader pre-training | Generic LED digits |
| LED Digital 1 (Roboflow) | 2,360 | Price digit reader | Generic LED display |
| Gas_Station Stela (Roboflow) | 6,754 | Finder transfer learning | Brazilian price pylons |

---

## Data Collection Roadmap

| Phase | Source | Target Count | Status |
|-------|--------|-------------|--------|
| **Seed** | Wikimedia Commons (downloaded) | 9 images | **DONE** |
| **Mine** | Wikimedia AU petrol categories | ~50-100 images | Pending |
| **Collect** | Manual photography | 100-200 images | Not started |
| **Scrape** | Google Street View API | 200-500 images | Not started |
| **Auxiliary** | 7-segment Roboflow datasets | ~8,100 crops | Not started |

---

## Observations from Real Images

1. **Price format**: Always `XXX.X` cents/litre (3 digits + dot + 1 digit). LPG can be `XX.X`.
2. **Sign technologies**: LED red digits (most common), LED blue/white, backlit static, mechanical flip, full-color digital
3. **Promotional overlays**: Common — "Save 4c" with Woolworths/Coles logos, affects bounding box layout
4. **Branded fuel names**: V-Power (Shell), Vortex (Ampol), Amplify (EG) — need aliases in fuel_types.yaml
5. **Entry count**: Typically 3-5 fuel types per sign
6. **Night appearance**: LED signs glow brightly against dark sky — very different from daytime
