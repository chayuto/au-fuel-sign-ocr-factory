# Scrape Report — State+Brand Queries
**Batch:** `batch_statebrand_20260409T074033`
**Date:** 2026-04-09
**Strategy:** Wikimedia Commons category traversal — Australian fuel station brands

## Summary
- **Total downloaded:** 32 images
- **Sources:** Wikimedia Commons (all CC-licensed)
- **Search queries used:** State+brand combinations, Wikimedia Commons categories for AU petrol stations
- **Categories traversed:**
  - `Category:Petrol_stations_in_Victoria,_Australia`
  - `Category:BP_petrol_stations_in_Australia`
  - `Category:Shell_petrol_stations_in_Australia`
  - `Category:Ampol_petrol_stations_in_Australia`
  - `Category:Caltex_petrol_stations_in_Australia`
  - `Category:United_Petroleum`
  - `Category:Petrol_stations_in_Queensland`
  - `Category:Gasoline_price_boards`

---

## Visual QA Assessment

### ACCEPT — Price sign visible, recommend for labeling pipeline (17 images)

| Filename | Brand | State | Notes |
|----------|-------|-------|-------|
| wiki_united_brisbane_qld_price_2020.jpg | United | QLD | EXCELLENT — pylon close-up: E10 83.9, Unleaded 87.9, Diesel 121.9 |
| wiki_united_brisbane_qld_oil_2026.jpg | United | QLD | GOOD — station wide shot with pylon showing 233.9/241.9/295.9 |
| wiki_coles_express_prices_wallsend_nsw.jpg | Coles Express | NSW | EXCELLENT — pylon with E10 139.9, Unleaded 141.4, V-Power 164.9, Diesel 136.9, Autogas |
| wiki_mobil_albury_nsw_2024.jpg | Mobil | NSW | EXCELLENT — pylon close-up with E10/Unleaded/Supreme98/Diesel prices |
| wiki_shell_leonora_wa_2018.jpg | Shell/Coles Express | WA | GOOD — rural WA pylon with Unleaded 179.9, Diesel 176.9 |
| wiki_shell_tolland_nsw_2026.jpg | Shell | NSW | EXCELLENT — tall pylon LED sign with 244.9/269.5/299.5 |
| wiki_ampol_apollo_bay_vic_2023_a.jpg | Ampol | VIC | GOOD — Ampol pylon with green LED prices visible |
| wiki_ampol_apollo_bay_vic_2023_b.jpg | Ampol | VIC | GOOD — wider shot, Ampol pylon with prices |
| wiki_eg_ampol_sunshine_vic_2022.jpg | EG Ampol | VIC | EXCELLENT — EG Ampol pylon with full price board (E10/Ampol 91/Ampol Diesel/LPG) |
| wiki_bororen_ampol_qld.jpg | Ampol | QLD | GOOD — small-town Ampol QLD with pylon showing 3 prices |
| wiki_shell_otr_lane_cove_nsw_2023_b.jpg | Shell/OTR | NSW | GOOD — Shell/OTR pylon with price board visible (first OTR in NSW) |
| wiki_caltex_rockhampton_qld.jpg | Caltex | QLD | GOOD — Caltex pylon sign visible (Rockhampton QLD) |
| wiki_shell_bright_vic_2022.jpg | Shell | VIC | GOOD — Shell VIC with pylon LED price board visible |
| wiki_shell_aspley_qld.jpg | Shell | QLD | GOOD — dramatic night shot with pylon showing LED prices |
| wiki_ampol_nambour_qld_2023.jpg | Ampol | QLD | GOOD — night shot Ampol QLD with tall pylon sign visible |
| wiki_ampol_gosnells_wa.jpg | Ampol | WA | GOOD — dusk shot Ampol WA with pylon sign visible |
| wiki_bp_innisfail_qld_2025.jpg | BP | QLD | GOOD — night BP QLD with pylon sign and price board |

### MARGINAL — Station visible, price sign absent or too small (15 images)
*Still useful for brand classifier / station context, but won't pass labeling screen*

| Filename | Brand | State | Issue |
|----------|-------|-------|-------|
| wiki_liberty_werribee_vic_2022_a.jpg | Liberty | VIC | Good Liberty station shots but no price sign visible |
| wiki_liberty_werribee_vic_2022_b.jpg | Liberty | VIC | No price board |
| wiki_liberty_werribee_vic_2022_c.jpg | Liberty | VIC | Distant price pylon, small |
| wiki_puma_truganina_vic_2022.jpg | Puma | VIC | No price board (pre-rebrand to Caltex) |
| wiki_caltex_truganina_vic_2023.jpg | Caltex | VIC | No price board in frame |
| wiki_united_kewdale_wa.jpg | United | WA | Station forecourt only |
| wiki_shell_otr_lane_cove_nsw_2023_a.jpg | Shell/OTR | NSW | Wide forecourt, no price sign |
| wiki_shell_nsw_night_2024.jpg | Shell/Coles Express | NSW | Night station, price board not in frame |
| wiki_bp_night_adelaide_sa_2020.jpg | BP | SA | Night BP, no price board |
| wiki_bp_semaphore_sa_2026.jpg | BP | SA | Station exterior, no price board |
| wiki_bp_port_hedland_wa_2023.jpg | BP | WA | Inside forecourt close-up, no price board |
| wiki_bp_cunnamulla_qld.jpg | BP | QLD | Small rural station, no price board |
| wiki_pacific_petroleum_blacksoil_qld_2023.jpg | Pacific Petroleum | QLD | Distant fuel depot, very small |
| wiki_caltex_preston_vic_2022.jpg | Caltex | VIC | Wide shot, no price board visible |
| wiki_caltex_springvale_vic_2022.jpg | Caltex | VIC | Wide shot, no price board visible |

---

## Brand Coverage
| Brand | Count | States |
|-------|-------|--------|
| Ampol/EG Ampol | 6 | VIC, QLD, WA |
| Caltex | 4 | VIC, QLD |
| Shell/Coles Express/Shell OTR | 6 | NSW, QLD, VIC, WA |
| United | 3 | QLD, WA |
| BP | 4 | QLD, SA, WA |
| Liberty | 3 | VIC |
| Mobil | 1 | NSW |
| Puma | 1 | VIC |
| Pacific Petroleum | 1 | QLD |
| **Total** | **32** | **NSW, VIC, QLD, WA, SA** |

## Gaps Remaining
- OTR standalone (SA) — only found Shell/OTR hybrid in NSW
- 7-Eleven — none found (no free images on Wikimedia Commons)
- Costco — still 0
- Metro Petroleum — none found
- TAS coverage — none found

## License
All images sourced from Wikimedia Commons under Creative Commons licenses (CC BY-SA 4.0 or CC0). No PII, no watermarks, fully distributable.
