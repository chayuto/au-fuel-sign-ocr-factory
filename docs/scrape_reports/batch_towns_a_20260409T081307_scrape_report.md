# Scrape Report: Varied Town Queries Batch A (Regional AU)

**Date:** 2026-04-09
**Batch directory:** `data/ingest/batch_towns_a_20260409T081307`
**Total accepted images:** 22
**Total rejected:** ~30 (pump close-ups, composites, signs too small, no price boards)

## Summary

Searched across 20 regional town query variants targeting Townsville, Cairns, Toowoomba, Geelong, Ballarat, Bendigo, Wollongong, Newcastle, Gold Coast, Sunshine Coast, Darwin, Hobart, Launceston, Dubbo, Wagga Wagga, Albury, Tamworth, Rockhampton, Mackay, and Bunbury.

Primary source: Wikimedia Commons (via MediaSearch API) — most images from category pages for United Petroleum, Ampol, Shell, BP, Liberty, 7-Eleven/Mobil stations.

Secondary sources: news/blog image URLs (Daily Mail, CarsalesEditorial, CV Media Signage, CQ Today).

## Query Set Coverage

Queries were issued for all 20 target towns. Direct photo results were sparse for specific regional towns — most yielded fuel price tracking websites rather than images. The Wikimedia Commons approach produced the most usable results.

## Accepted Images (22)

| File | Brand | Location | State | Year | Notes |
|------|-------|----------|-------|------|-------|
| `news_carsales_diesel_priceboard_au.jpg` | BP | Unknown | AU | ~2024 | Green BP sign, U91 221.9/Ult98 232.9/Diesel 221.9 |
| `news_dailymail_fuelcrisis_999_au_2026.jpg` | Ampol | Unknown | AU | 2026 | 999.9 placeholder all rows (fuel shortage marker) |
| `news_dailymail_fuelcrisis_sign_au_2026_2.jpg` | Liberty | Unknown | AU | 2026 | E10 999.9, U91 185.5, Diesel 205.9 |
| `web_otr_pylon_au_2024.jpg` | OTR | Unknown | SA | 2024 | Unleaded 193.9, Diesel 211.9 |
| `wiki_7eleven_shortland_nsw.jpg` | 7-Eleven/Mobil | Shortland | NSW | 2018 | E10 135.9/U 137.9/98 155.9/Diesel 137.9 |
| `wiki_ampol_bororen_qld.jpg` | Ampol | Bororen | QLD | ~2022 | 3-row prices, 172.x/186.x/199.x |
| `wiki_bp_emupark_qld_1.jpg` | BP | Emu Park | QLD | 2022 | Pylon visible, prices partial |
| `wiki_bp_emupark_qld_2.jpg` | BP | Emu Park | QLD | 2022 | 3-row prices visible |
| `wiki_bp_innisfail_qld_2025_2.jpg` | BP | Innisfail | QLD | 2025 | Night, prices ~171.5 visible |
| `wiki_bp_norseman_wa_2017.jpg` | BP | Norseman | WA | 2017 | 3-row sign: ~148/146/122 |
| `wiki_egampol_sunshine_vic_2022.jpg` | EG Ampol | Sunshine | VIC | 2022 | U91 174.9/95 187.9/Diesel 225.9/LPG 89.9 |
| `wiki_fuelprices_prestonbeach_wa_2013.jpg` | Regional | Preston Beach | WA | 2013 | Unleaded 172/Diesel 170 panel sign |
| `wiki_liberty_birminghamgardens_nsw.jpg` | Liberty | Birmingham Gardens | NSW | ~2018 | E10 135.9/U91 137.9/Diesel 131.9 |
| `wiki_mobil_albury_nsw_2024.jpg` | Mobil | Albury | NSW | 2024 | E10 176.9/U 178.9/98 198.9/Diesel 188.9 |
| `wiki_mobil_priceboard_au.jpg` | Mobil | Unknown | AU | ~2013 | 139.0 visible, low-res but real |
| `wiki_roadhouse_mundrabilla_wa_2017.jpg` | Regional | Mundrabilla | WA | 2017 | U 161.0/Premium Diesel 161.0 |
| `wiki_shell_colesexpress_hobart_tas.jpg` | Shell/Coles Express | Hobart | TAS | ~2015 | 3-row pylon, prices partially visible |
| `wiki_shell_colesexpress_wallsend_nsw.jpg` | Shell/Coles Express | Wallsend | NSW | ~2015 | E10 139.9/U 141.4/V-Power 164.9/Diesel 136.9/Autogas 79.9 |
| `wiki_shell_leonora_wa_2018.jpg` | Shell/Coles Express | Leonora | WA | 2018 | U 179.9/Diesel 176.9 |
| `wiki_shell_tolland_nsw_2026.jpg` | Shell | Tolland (Wagga Wagga) | NSW | 2026 | 249.5/269.5/299.5 — covers Wagga Wagga query |
| `wiki_united_brisbane_qld_2020.jpg` | United | Brisbane | QLD | 2020 | E10 83.9/U 87.9/Diesel 121.9 |
| `wiki_united_brisbane_qld_2026.jpg` | United | Brisbane | QLD | 2026 | 233.9/241.9/295.9 |

## Reject Reasons (representative)

- ~8 images: no price sign board visible (just station exterior/canopy)
- ~5 images: price sign too small (<15% frame)
- ~4 images: pump LCD close-ups (not sign boards)
- ~3 images: composite news images with politicians/mixed content
- ~2 images: non-sign board content (pumps, nozzles)
- ~2 images: prices unreadable (dark/blurry/night)

## Geographic Coverage

| State | Count |
|-------|-------|
| NSW | 6 (Shortland, Birmingham Gardens, Wallsend, Albury, Tolland/Wagga Wagga) |
| QLD | 7 (Brisbane x2, Bororen, Emu Park x2, Innisfail) |
| VIC | 2 (Sunshine) |
| WA | 5 (Preston Beach, Mundrabilla, Leonora, Norseman) |
| TAS | 1 (Hobart) |
| SA | 1 (OTR unknown location) |
| AU (unspecified) | 2 |

## Brand Coverage

BP (5), Shell/Coles Express (4), United (2), Mobil (3), Ampol (3), Liberty (2), OTR (1), 7-Eleven/Mobil (1), Regional (2)

Note: Costco remains at 0 (none found).

## Notes

- 2026 fuel crisis images captured 999.9 placeholder prices — useful for training as real sign board structure
- Strong WA outback/roadhouse coverage (Mundrabilla, Leonora, Norseman, Preston Beach)
- Shell Tolland specifically covers the Wagga Wagga NSW query
- Hobart TAS covered (one image — scarce source)
