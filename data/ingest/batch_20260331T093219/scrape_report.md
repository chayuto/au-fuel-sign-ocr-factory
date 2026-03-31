# Scrape Report: v4 Slot 2 — Wikimedia State-by-State Deep Dive

## Summary
- **Images saved:** 3
- **Images rejected:** 14 (with reasons)
- **Brands covered:** independent, mobil
- **Hit rate by source:** wikimedia → 3 saved / 17 attempted (17.6%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| File:MobilPriceBoard.png | saved | 1 | size=324690; type=png image data, 640 x 480, 8-bit/color rgb, non-interlaced; src=WA category; url=https://upload.wikimedia.org/wikipedia/commons/c/c4/MobilPriceBoard.png |
| File:BP petrol station, Port Hedland, 2023.jpg | skipped_dedup | 0 | keyword=port; hits=1 |
| File:Pacific Petroleum Blacksoil 2023.jpg | saved | 1 | size=3022909; type=jpeg image data, exif standard: [tiff image data, little-endian, direntries=11, manufacturer=samsung, model=sm-g950f, orientation=upper-left, xresolution=146, yresolution=154, resolutionunit=2, software=g950fxxucdvg4, datetime=2023:08:06 13:18:09, gps-data], baseline, precision 8, 4032x2268, components 3; src=QLD category; url=https://upload.wikimedia.org/wikipedia/commons/4/43/Pacific_Petroleum_Blacksoil_2023.jpg |
| File:Petrol station, Lockhart River, Queensland, 2025.jpg | saved | 1 | size=3056818; type=jpeg image data, jfif standard 1.01, resolution (dpi), density 300x300, segment length 20, exif standard: [tiff image data, big-endian, direntries=12, photometricinterpretation=(unknown=0x884c), manufacturer=apple, model=iphone 15 pro max, orientation=upper-left, xresolution=182, yresolution=190, resolutionunit=2, software=18.2.1, datetime=2025:01:19 14:09:50, gps-data], baseline, precision 8, 3911x2933, components 3; src=QLD category; url=https://upload.wikimedia.org/wikipedia/commons/c/ca/Petrol_station%2C_Lockhart_River%2C_Queensland%2C_2025.jpg |
| File:Oil price hikes during the 2026 Iran war in March 2026, Brisbane.jpg | rejected | 0 | download_status_429 |
| File:Caltex servo Rockhampton.jpg | rejected | 0 | download_status_429 |
| File:KoongalServo1.jpg | rejected | 0 | download_status_429 |
| File:KoongalServo2.jpg | rejected | 0 | download_status_429 |
| File:MtLarcomServo2.jpg | rejected | 0 | download_status_429 |
| File:MtLarcomServo3.jpg | rejected | 0 | download_status_429 |
| File:Yellowdine fuel station.jpg | rejected | 0 | download_status_429 |
| File:Wandering Petrol Station, October 2020.jpg | rejected | 0 | download_status_429 |
| File:Dardanup service station 2020.jpg | rejected | 0 | download_status_429 |
| File:Shell Service Station, Upper Swan, WA.jpg | rejected | 0 | download_status_429 |
| File:BP fuel station Jandakot airport.jpg | rejected | 0 | download_status_429 |
| File:Shell fuel station Jandakot airport.jpg | rejected | 0 | download_status_429 |
| File:Petrol station on the corner of Mort and Cooyong Streets April 2025.jpg | rejected | 0 | download_status_429 |

## What Worked
- Wikimedia category file pages from QLD/WA yielded multiple modern station images with visible signage.
- Using Wikimedia API with explicit user-agent avoided 403 responses and enabled direct image URL retrieval.
- MIME/type + size checks filtered non-image/error payloads.

## What Didn't Work
- Several slot-2 categories were empty for file namespace (TAS, NT, Fuel_prices_in_Australia).
- Some category files are historical and likely low utility for modern LED price-sign training.

## Suggestions for v5
- Traverse subcategories/pages in SA/QLD/WA categories (not just direct File namespace) to discover additional images.
- Combine state category crawl with targeted Wikimedia search queries for OTR/Metro/Costco within SA/QLD/WA.
- Prioritize 2023+ uploads and files with explicit `price board`, `fuel`, `servo`, or brand keywords in title.