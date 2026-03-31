# Scrape Report: v4 Slot 3 — Wikimedia Night & Weather Conditions

## Summary
- **Images saved:** 7
- **Images rejected:** 0
- **Brands covered:** bp, liberty, shell, ampol, caltex
- **Hit rate by source:** Wikimedia Commons API/FilePath → 7 saved / 7 attempted (100%)

## Sources Attempted

| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `"petrol station night" Australia` (Wikimedia API search, namespace 6) | success | 3 candidates used | Returned key night files including BP/Liberty/Service Station at Night |
| `"fuel station dusk" Australia` | success | 0 | No useful file hits |
| `"servo night" Australia` | success | 0 | Mostly non-image/noisy results |
| `"fuel price LED night" Australia` | success | 0 | No useful file hits |
| `"petrol station rain" Australia` | success | 0 | Mostly unrelated/noisy results |
| `"service station evening" Australia` | success | 0 | No usable fuel sign images |
| Wikimedia file metadata lookups (`action=query&prop=imageinfo`) for shortlisted files | success | 7 validated | Confirmed direct file URLs and image metadata |
| Direct downloads via `Special:FilePath` | success (with retries) | 7 saved | Encountered intermittent 429 rate limits; retries succeeded |

## What Worked
- Night-focused query `petrol station Australia night` surfaced the strongest candidates.
- Wikimedia file metadata endpoint (`imageinfo`) was reliable for resolving direct URLs.
- `Special:FilePath` download path with retries handled intermittent 429 responses.
- All saved files passed validation checks (`file` MIME starts with `image/`, size > 5 KB).

## What Didn't Work
- Slot-provided category names (`Night_photographs_in_Australia`, `Photographs_taken_at_night`) returned no file members via API in this environment.
- Most rain/dusk/evening text queries had very high noise (PDF/DJVU/non-fuel content).
- Commons rate limiting intermittently blocked sequential direct downloads without retry delay.

## Suggestions for v5
- Add backoff/jitter between Wikimedia downloads by default to reduce 429s.
- Use category or template filters around `Petrol stations in Australia at night` for higher precision.
- Combine slot-3 lighting filters with slot-1 gap-brand constraints (e.g., `Costco fuel night Australia`, `OTR at night`) to improve strategic value.
- Consider collecting additional night images from non-Wikimedia high-yield sources (news/YouTube) once Wikimedia night supply is exhausted.
