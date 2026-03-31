# Scrape Report: v4 Slot 3 — Wikimedia Night & Weather

## Summary
- **Images saved:** 4
- **Images rejected:** 10 (HTML/Wikimedia error response instead of image)
- **Brands covered:** Shell, BP, Liberty, Ampol
- **Hit rate by source:** Wikimedia Commons API/search → 4 saved / 14 attempted (28.6%)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `"petrol station Australia night"` (Wikimedia file search) | success | 4 | Produced most useful candidates; found AU night station photos |
| `"fuel station dusk Australia"` | failed | 0 | Mostly archival PDFs/books, no usable station images |
| `"service station night Australia"` | partial | 0 new | Mostly rail/fire-station noise; one overlap candidate |
| `"fuel price sign night Australia"` | failed | 0 | Search noise; almost entirely non-image PDFs |
| `"petrol station rain Australia"` | failed | 0 | No usable fuel-sign images found |
| `Category:Night_photographs_in_Australia` (categorymembers) | failed | 0 | No directly useful station sign files surfaced |
| `Category:Petrol_stations_in_Australia_at_night` (categorymembers) | success | 4 | Confirmed candidate set for this slot |
| Wikimedia direct image URLs from candidates | partial | 4 | Some direct URLs returned Wikimedia error HTML; validated and rejected |

## What Worked
- Querying Wikimedia Commons with **night-focused terms** surfaced valid Australian fuel station night images.
- Using `prop=imageinfo&iiprop=url` API calls before download improved reliability for valid files.
- File validation guardrail (`file` MIME + size >5KB) correctly rejected non-image HTML error pages.

## What Didn't Work
- Many Wikimedia search queries returned high-noise PDFs and non-fuel content.
- Several candidate direct URLs intermittently returned Wikimedia error HTML (not image payload).
- Rain/dusk-specific queries had very low precision for Australian fuel price sign boards.

## Suggestions for v5
- Start directly from `Category:Petrol_stations_in_Australia_at_night` and recurse related subcategories to reduce query noise.
- Add category pivots for underrepresented brands + night (e.g., OTR/Metro/Costco brand pages + night keywords).
- Add retry/backoff and alternate imageinfo lookups (`iiurlwidth`) when direct URLs return transient Wikimedia error pages.
