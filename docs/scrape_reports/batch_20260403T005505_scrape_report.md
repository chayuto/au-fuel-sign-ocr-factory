# Scrape Report: v4 Slot 9 — Forums (Whirlpool / OzBargain)

## Summary
- **Images saved:** 10
- **Images rejected:** 2
  - 1 dedup skip (filename keyword already present)
  - 1 invalid image (< 5KB)
- **Brands covered:** costco, ampol, shell, independent
- **Hit rate by source:**
  - OzBargain direct/upload image URLs → 10 saved / 12 attempted (**83.3%**)
  - Whirlpool thread search → 0 saved / 0 attempted (used for discovery only; no direct downloadable station-photo URLs extracted in this run)

## Sources Attempted
| URL/Query | Result | Images | Notes |
|-----------|--------|--------|-------|
| `site:whirlpool.net.au "fuel price" sign photo` (via Whirlpool search endpoints) | partial | 0 | Returned many archive thread links, but no direct, immediately downloadable station sign images extracted in this batch window |
| `https://www.ozbargain.com.au/search/node/fuel%20price%20servo` | success | 3 | Found node `954318` with usable uploaded and cover images |
| `https://www.ozbargain.com.au/search/node/costco%20fuel` | success | 2 | Found node `953381` including a high-resolution uploaded screenshot |
| `https://www.ozbargain.com.au/search/node/liberty%20fuel` and related forum-result nodes | partial | 0 | Candidate pages found; selected only images passing size/type checks and relevance in this run |
| `https://www.ozbargain.com.au/search/node/otr%20fuel` and related forum-result nodes | partial | 0 | Candidate pages found; no additional valid downloads added beyond accepted set |
| `https://www.ozbargain.com.au/search/node/puma%20fuel` and related forum-result nodes | partial | 0 | Candidate pages found; no additional valid downloads added beyond accepted set |
| `https://www.ozbargain.com.au/node/944839` and `https://www.ozbargain.com.au/node/903617` | success | 4 | Freedom/independent station screenshots and cover images, valid size/type |
| `https://www.ozbargain.com.au/node/809224` | success | 1 | Shell-focused forum/deal image passed validation |

## What Worked
- OzBargain nodes often expose higher-quality original images under `/upload/...` paths.
- Combining node cover images (`/n/...jpg`) with `/upload/...` originals improved usable yield.
- File validation gates (size and MIME type) effectively filtered low-value assets.

## What Didn't Work
- Whirlpool search produced many discussion threads but not quick direct image URLs during this run.
- Some candidate images were too small to be useful (<5KB).
- Forum search noise remains high; many posts are fuel discussion without clear station-board photos.

## Suggestions for v5
- For Whirlpool, parse thread pages specifically for `i.postimg.cc`, `imgur`, and direct attachment hosts where user photos are commonly embedded.
- Continue prioritizing OzBargain nodes with explicit uploaded screenshots (`/upload/...`) over thumbnail-only result pages.
- Add a second-pass manual visual filter to rank by sign-board area and readability before labeling.
