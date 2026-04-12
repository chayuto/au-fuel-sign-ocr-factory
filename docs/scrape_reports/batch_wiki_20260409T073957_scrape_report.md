# Scrape Report — Wikimedia Gap Brands + State Categories

**Batch:** `data/ingest/batch_wiki_20260409T073957`
**Date:** 2026-04-09
**Agent:** Scraping agent (Sonnet)

## Summary

| Metric | Count |
|--------|-------|
| Images saved (accepted) | 30 |
| Images rejected | ~65 |
| Total downloaded and inspected | ~95 |

## Images Saved

| Filename | Brand | State | Notes |
|----------|-------|-------|-------|
| wiki_otr_alphington_vic_01.jpg | OTR | VIC | OTR pylon with LED prices 116.9 / 189.9 |
| wiki_caltex_otr_keilor_park_vic.jpg | Caltex / OTR | VIC | Caltex+OTR dual-brand, price sign visible |
| wiki_shell_otr_lane_cove_nsw_02.jpg | Shell / OTR | NSW | Shell pylon with multi-fuel LED prices |
| wiki_mobil_price_board_wa.jpg | Mobil | WA | Close-up price board, 139.0 / 59.0 / 140.0 |
| wiki_mobil_albury_nsw_02.jpg | Mobil | NSW | Pylon: E10 176.9, ULP 178.9, 98 198.9, Diesel 188.9 |
| wiki_liberty_birmingham_gardens_nsw.jpg | Liberty | NSW | Pylon: E10 135.9, ULP 137.9, Diesel 131.9 |
| wiki_liberty_oil_werribee_vic_03.jpg | Liberty | VIC | Liberty pylon with LED prices visible |
| wiki_puma_truganina_vic_03.jpg | Puma | VIC | Pylon: E10 187.7, ULP 189.7, Diesel 223.7 |
| wiki_coles_express_wallsend_nsw.jpg | Shell/Coles | NSW | 5 fuels: E10 139.9, ULP 141.4, V-Power 164.9, Diesel 136.9, Autogas 73.9 |
| wiki_coles_express_au.jpg | Shell/Coles | NSW | Night shot: ULP 124.9, 126.9, 136.9, 165 visible |
| wiki_coles_express_vermont_south_vic.jpg | Shell/Coles | VIC | Discount ULP 145.9, ULP 149.9, Diesel 154.9, Autogas 68.9 |
| wiki_coles_express_hobart_tas.jpg | Shell/Coles | TAS | First Tasmania image — prices visible |
| wiki_shell_leonora_wa_2018.jpg | Shell/Coles | WA | Pylon: Unleaded 179.9, Diesel 176.9 |
| wiki_shell_tolland_nsw_2026.jpg | Shell | NSW | 3 prices: 244.9, 269.9, 299.9 (2026 war pricing) |
| wiki_shell_bright_vic.jpg | Shell | VIC | LED prices visible on pylon |
| wiki_bp_petrol_station_au.jpg | BP | NSW/ACT | Ultimate, ULP 155.9, Diesel 171.9, Autogas 66.9 |
| wiki_bp_norseman_wa_2017.jpg | BP | WA | Pylon: Unleaded 148.0, Diesel 146.0, 122.9 |
| wiki_bp_wubin_roadhouse_wa.jpg | BP | WA | Yellow LED: 147.8, 147.3, 155.2 |
| wiki_bp_broome_wa.jpg | BP | WA | Pylon: ULP 91 229.9, Diesel 229.9, P95 246.9 |
| wiki_bp_emu_park_qld.jpg | BP | QLD | Price board visible on pylon |
| wiki_ampol_apollo_bay_vic_01.jpg | Ampol | VIC | Pylon: 203.1, 217.x, 225.x |
| wiki_eg_ampol_sunshine_vic.jpg | EG Ampol | VIC | Pylon: ULP91 174.9, Ampol95 187.9, Diesel 225.9, LPG 89.9 |
| wiki_caltex_woolworths_au_2020.jpg | Caltex/Woolworths | WA | Green LED pylon with prices |
| wiki_caltex_sunbury_vic_01.jpg | Caltex | VIC | Pylon: 171.9, 178.9, 235.9 |
| wiki_caltex_sunbury_vic_02.jpg | Caltex | VIC | Pylon: 177.9, 179.9, 235.9 |
| wiki_caltex_truganina_vic_02.jpg | Caltex | VIC | Pylon: 162.5, 164.5, 192.5 |
| wiki_united_price_display_brisbane_qld_2020.jpg | United | QLD | E10 83.9, ULP 87.9, Diesel 121.9 (COVID pricing) |
| wiki_fuel_prices_brisbane_qld_2026.jpg | United | QLD | 239.9, 247.9, 295.9 (war pricing) |
| wiki_fuel_prices_preston_beach_wa.jpg | Generic/Thirsty Camel | WA | UNLEADED 172.0, DIESEL 170.0 |
| wiki_mundrabilla_roadhouse_wa.jpg | Regional | WA | UNLEADED 161.0, PREMIUM DIESEL 161.0 |

## Rejection Reasons

| Category | Count |
|----------|-------|
| No price sign board visible (forecourt/canopy only) | ~35 |
| Price sign too small / distant (<15% of image) | ~15 |
| Interior shot or pump dispenser | ~5 |
| Heritage/pre-1990s station | 0 |
| Night shot with no readable sign | ~5 |
| Non-Australian station | 0 |
| Screenshot/editorial | 0 |

## Brands Covered

| Brand | New Images |
|-------|-----------|
| OTR (On The Run) | 2 |
| Mobil | 2 |
| Liberty | 2 |
| Puma | 1 |
| Shell / Coles Express | 6 |
| BP | 5 |
| Ampol / EG Ampol | 2 |
| Caltex / Caltex Woolworths | 5 |
| United | 2 |
| Regional / Roadhouse | 2 |
| Unknown/Generic | 1 |

**Note:** Costco fuel images not found on Wikimedia Commons — Costco Australia stations have no Wikimedia coverage. Metro Petroleum also absent from Commons.

## Sources Attempted

| Source | Method | Files Found | Useful |
|--------|--------|-------------|--------|
| Wikimedia search: "Costco fuel Australia" | API search | 0 image | 0 |
| Wikimedia search: "OTR fuel Australia" | API search | 16 | 11 downloaded |
| Wikimedia search: "Metro Petroleum price" | API search | 0 image | 0 |
| Wikimedia search: "Liberty fuel Australia" | API search | 0 image | 0 |
| Category:Petrol_stations_in_Queensland | Cat crawl | 53 | 1 |
| Category:Petrol_stations_in_Western_Australia | Cat crawl | 28 | 5 |
| Category:Petrol_stations_in_South_Australia | Cat crawl | 11 | 1 |
| Category:Petrol_stations_in_Tasmania | Cat crawl | 0 | 0 |
| Category:Petrol_stations_in_Northern_Territory | Cat crawl | 0 | 0 |
| Category:Petrol_stations_in_New_South_Wales | Cat crawl | 62 | 4 |
| Category:Petrol_stations_in_Victoria,_Australia | Cat crawl | 57 | 7 |
| Category:OTR_(convenience_store) | Cat crawl | 16 | 2 |
| Category:Ampol_petrol_stations_in_Australia | Cat crawl | 8 | 3 |
| Category:BP_petrol_stations_in_Australia | Cat crawl | 33 | 5 |
| Category:Caltex_petrol_stations_in_Australia | Cat crawl | 52 | 5 |
| Category:Shell_petrol_stations_in_Australia | Cat crawl | 33 | 4 |
| Category:United_Petroleum | Cat crawl | 4 | 2 |
| Category:Puma_petrol_stations_in_Australia | Cat crawl | 12 | 2 |
| Category:Mobil_petrol_stations_in_Australia | Cat crawl | 11 | 2 |
| Category:Petrol_stations_in_Australia_at_night | Cat crawl | 8 | 1 |
| Category:Roadhouses_in_Australia | Cat crawl | 20 | 1 |
