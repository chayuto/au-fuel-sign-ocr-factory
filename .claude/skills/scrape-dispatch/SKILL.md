---
name: scrape-dispatch
description: |
  Plans and executes scrape campaigns for Australian fuel station price sign images.
  Assesses current dataset state, brand gaps, and historical yield before recommending
  queries. Use this skill when the user wants to "scrape more", "collect images",
  "fill brand gaps", or "get more training data".
---

# Scrape Dispatch: Plan & Execute Image Collection

## Step 0: Assess Before Scraping (MANDATORY)

**Never scrape blind.** Before planning any queries, run this assessment:

### 0a. Dataset state

```bash
# Brand distribution in labeled annotations
.venv/bin/python -c "
import json, os
brands = {}
for fn in sorted(os.listdir('data/tmp/annotations')):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d: continue
    b = d['sign'].get('brand', 'unknown')
    brands[b] = brands.get(b, 0) + 1
for b, c in sorted(brands.items(), key=lambda x: -x[1]):
    print(f'{b:20s} {c:3d}')
print(f\"{'TOTAL':20s} {sum(brands.values()):3d}\")
"

# Manifest status
awk -F, 'NR>1{s[$2]++} END{for(k in s) print k, s[k]}' data/tmp/labeling_manifest.csv | sort

# Pending images (already ingested, waiting for labeling)
awk -F, 'NR>1 && $2=="pending"{c++} END{print "Pending:", c+0}' data/tmp/labeling_manifest.csv

# Ingest backlog
find data/ingest/ -name '*.jpg' -o -name '*.png' 2>/dev/null | wc -l
```

### 0b. Identify brand gaps

Compare current counts against targets. The model needs balanced representation.

**Minimum targets per brand (for reasonable generalization):**

| Tier | Brands | Target | Notes |
|------|--------|--------|-------|
| Major (high variety) | caltex, shell, bp, ampol | 50+ each | These are well-covered |
| Medium | mobil, seven_eleven, united, liberty, puma, metro, otr | 25+ each | Still growing |
| Minor (hard to find) | costco, eg, apco | 15+ each | Rare on web, may need manual |
| Catch-all | independent, unknown, other | 20+ combined | Already covered |

**Gap = target - current count.** Prioritize brands with the largest gap.

### 0c. Review scrape history & yield

```bash
# Recent scrape yields (from pipeline_events.jsonl)
.venv/bin/python -c "
import json
events = {}
try:
    with open('data/tmp/pipeline_events.jsonl') as f:
        for line in f:
            e = json.loads(line)
            agent = e.get('agent', '')
            if 'scrape' not in agent and 'sonnet_v5' not in agent: continue
            action = e.get('action', '')
            key = agent.split('_')[0:3]  # group by agent prefix
            k = '_'.join(key) if len(key) >= 3 else agent
            if k not in events: events[k] = {'labeled': 0, 'skipped': 0}
            if action == 'labeled': events[k]['labeled'] += 1
            elif action == 'skipped': events[k]['skipped'] += 1
except: pass
for k, v in sorted(events.items()):
    total = v['labeled'] + v['skipped']
    if total > 0:
        pct = v['labeled'] * 100 // total
        print(f'{k:30s} {v[\"labeled\"]:3d}/{total:3d} = {pct}% yield')
"
```

### 0d. Skip reason analysis

```bash
# Categorize why images were skipped (most recent round)
.venv/bin/python -c "
import json
cats = {'not_AU': 0, 'no_sign': 0, 'watermark': 0, 'mfr_render': 0, 'too_small': 0, 'composite': 0, 'logo_only': 0, 'pump': 0, 'other': 0}
try:
    with open('data/tmp/pipeline_events.jsonl') as f:
        for line in f:
            e = json.loads(line)
            if e.get('action') != 'skipped': continue
            r = (e.get('reason', '') or '').lower()
            if any(x in r for x in ['not au', 'non-au', 'french', 'canadian', 'uk ', 'us ', 'gallon', 'foreign', 'non-australian']): cats['not_AU'] += 1
            elif any(x in r for x in ['watermark', 'shutterstock', 'alamy', 'dreamstime', 'istock']): cats['watermark'] += 1
            elif any(x in r for x in ['manufacturer', 'manufacturing', 'render', 'cad']): cats['mfr_render'] += 1
            elif any(x in r for x in ['composite', 'editorial', 'infographic']): cats['composite'] += 1
            elif any(x in r for x in ['too small', 'too distant', 'distant']): cats['too_small'] += 1
            elif any(x in r for x in ['logo only', 'brand only']): cats['logo_only'] += 1
            elif any(x in r for x in ['pump', 'bowser', 'nozzle']): cats['pump'] += 1
            elif any(x in r for x in ['no price', 'no fuel', 'canopy', 'forecourt', 'no_price', 'no_fuel']): cats['no_sign'] += 1
            else: cats['other'] += 1
except: pass
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f'  {n:3d}x  {c}')
"
```

After running all 4 checks, present a summary table and recommend specific queries.

---

## Campaign Strategy: Always Winners + Variance

**RULE: Every scrape session must be ~60% proven winners + ~40% new experimental queries.**
Never scrape only one type. This prevents exhaustion of any single query pattern.

### Tier 0: Proven Winners (use EVERY session)

These queries consistently produce labeled images. Always include at least 3 of these:

| Query Pattern | Yield | Example |
|---------------|-------|---------|
| **APCO + regional VIC city** | **80%** | `"APCO fuel price sign Bendigo Ballarat Victoria"` |
| **EG Foodary + state** | **60%** | `"EG Foodary fuel price pylon Victoria"` |
| **Price war + Australia** | **33%** | `"petrol price war Australia sign board cheap fuel"` |
| **State-generic + LED pylon** | **25%** | `"fuel price board Tasmania Australia LED pylon"` |

### Tier 1: State+Brand (40-100% yield) — USE FIRST

The gold standard. Always include Australian state + brand + "fuel price sign".
**Use specific suburbs/cities, not just state names** — more specific = higher yield.

**Template:** `"{Brand} fuel price sign {City/Suburb} {State} Australia"`

```bash
# Best-performing examples (2026-04-11)
.venv/bin/python scripts/scrape_google_images.py --query "APCO fuel price sign Wodonga Bendigo Victoria" --brand apco_reg --max 20
.venv/bin/python scripts/scrape_google_images.py --query "EG Foodary fuel price pylon Gregory Hills NSW" --brand eg_sw --max 20
.venv/bin/python scripts/scrape_google_images.py --query "Metro Petroleum price board Bankstown Fairfield NSW" --brand metro_sw --max 20
```

**Best state+brand combos by brand gap:**

| Brand | Best states | Why |
|-------|------------|-----|
| apco | Victoria (regional) | APCO is VIC regional, Wodonga/Bendigo/Ballarat gold |
| eg | Victoria, NSW | "EG Foodary" keyword differentiates from generic "EG" |
| puma | Queensland | Puma is QLD-dominant, highest density |
| otr | South Australia | OTR is SA-only but VERY hard to find (mostly marketing shots) |
| liberty | Victoria, Western Australia | Liberty stronghold states |
| eg | Victoria, New South Wales | EG Ampol operates nationally |
| metro | New South Wales, Victoria | Metro Petroleum is NSW/VIC |
| united | Victoria, Queensland | United is national but VIC/QLD strongest |
| costco | Victoria, NSW, ACT | Only ~10 Costco fuel sites in AU |
| apco | Victoria, NSW | APCO is VIC/NSW regional |

### Tier 2: News + Location (25-40% yield)

News articles about fuel prices often have station photos with visible price boards.

**Template:** `"fuel price {brand} {city} site:{news_domain}"`

```bash
.venv/bin/python scripts/scrape_google_images.py --query "fuel price Costco Canberra site:canberratimes.com.au" --brand costco --max 20
.venv/bin/python scripts/scrape_google_images.py --query "petrol price OTR Adelaide site:adelaidenow.com.au" --brand otr --max 20
```

### Tier 3: Flickr Photographers (30-50% yield)

Specific Flickr users who photograph Australian fuel stations. High quality but limited pool.

Known good photographers (from batch_flickr_20260409):
- thetransitcamera, waggalibrary, westographer, mikecogh, pwpix, ajft

### Tier 4: Generic Brand (10-25% yield) — LAST RESORT

Only when tiers 1-3 are exhausted. Must add "Australia" to avoid international noise.

**Template:** `"{Brand} Australia fuel station price sign LED pylon -manufacturer -stock"`

**Critical:** Add `-manufacturer -stock -alibaba -made-in-china` to reduce Chinese LED sign factory images.

---

## Empirical Yield Table (from 1700+ images, 2026-04-11)

**Top performers (>50% yield):**

| Query | Done | Skip | Yield | Notes |
|-------|------|------|-------|-------|
| seven_eleven (generic) | 9 | 1 | 90% | Excellent, but exhausted |
| apco_vic | 11 | 0 | 100% | Best new source, VIC APCO |
| puma_qld2 (Rockhampton) | 7 | 1 | 87% | City-specific works for Puma |
| bp_qld | 5 | 0 | 100% | State+brand gold |
| vic (generic) | 10 | 5 | 66% | VIC state queries reliable |
| wa | 6 | 2 | 75% | WA queries work |
| nsw | 6 | 3 | 66% | NSW queries work |
| liberty_vic | 4 | 2 | 66% | VIC Liberty |
| 7eleven_vic | 5 | 3 | 62% | VIC 7-Eleven |
| united_vic | 3 | 2 | 60% | VIC United |
| coles | 13 | 10 | 56% | Coles Express |
| liberty (generic) | 11 | 9 | 55% | With "Australia" |
| apco (generic) | 12 | 11 | 52% | Regional AU brand |
| costco_act | 4 | 4 | 50% | ACT catches nearby signs |
| 7eleven_nsw | 4 | 4 | 50% | NSW 7-Eleven |

**Moderate (20-50%):**

| Query | Done | Skip | Yield | Notes |
|-------|------|------|-------|-------|
| eg_vic | 5 | 2 | 71% | Finds Ampol/EG stations |
| eg (generic) | 9 | 13 | 40% | Many non-AU results |
| caltex2 | 11 | 17 | 39% | Good but diminishing |
| otr (generic) | 18 | 34 | 34% | Mix of real + marketing |
| metro | 13 | 28 | 31% | Many non-AU |

**Zero yield (RETIRED — DO NOT USE):**

| Query | Tried | Why it fails |
|-------|-------|-------------|
| otr_news | 30 | Returns OTR sports sponsorship thumbnails (football, cricket, MotoGP) |
| otr_sa (any variant) | 50+ | Marketing shots, forecourts, non-AU Shell pylons. OTR is nearly impossible via Bing. |
| otr_south (Morphett Vale etc) | 12 | Returns EU/US Shell signs, not OTR |
| Costco AU (any variant) | 40+ | US Costco dominates all results (only ~10 AU Costco fuel sites exist) |
| Liberty (generic, no state) | 15 | Returns US Liberty brand, not AU |
| NT/Darwin fuel queries | 8 | Returns Irish "Jones Oil", non-AU brands |
| puma_qld (generic) | 5 | Africa, PNG, non-AU Puma Energy |
| eg_nsw / eg (generic) | 20 | Heavy non-AU pollution (US, UK, manufacturer) — use "EG Foodary" instead |
| United Brisbane (generic) | 5 | Station exteriors only, no price signs |
| acapma | 17 | Industry body, no station photos |
| au_led | 10 | Chinese LED manufacturer products |
| bp2 | 14 | South Africa, vintage pumps |
| closeup | 14 | LED module products, not stations |
| suburb_* (all) | ~20 | Hardware stores, aerial photos |
| cheap/outrage2 | ~23 | Infographics, charts, memes |
| Flickr heritage groups | — | 100% vintage, no modern signs |
| night_au (generic) | 1 | Returns unrelated night photos |

## Known Pollution Patterns

**Chinese LED manufacturers** — Foshan Guose, Grandview, Buoyant Signage, made-in-china.com, alibaba.com. These appear in ~15% of Bing results for any "fuel price sign" query. Add `-manufacturer -alibaba -"made in china" -Guose -Grandview` to queries.

**Non-AU stations** — US (dollar/gallon), UK (pence/litre), France (Carrefour), PNG (toea), South Africa (BP SA). The "Australia" keyword doesn't always filter these. State names (Victoria, Queensland) are more effective than "Australia".

**Stock photo watermarks** — Shutterstock, Alamy, Dreamstime, iStock, Getty, Bloomberg. ~13% of skips. Some watermarked images are still usable if the sign is clearly readable.

**OTR sports sponsorship** — OTR sponsors Australian sports teams. Any query combining "OTR" with news sites returns football, cricket, MotoGP images. Must use "OTR fuel PRICE" not "OTR news".

---

## Running a Scrape Campaign

### 1. Plan queries based on assessment

After running Step 0, generate a query list targeting the biggest gaps:

```bash
# Run multiple queries in parallel (one per brand gap)
.venv/bin/python scripts/scrape_google_images.py --query "Puma fuel price sign Queensland Australia pylon LED" --brand puma --max 30 &
.venv/bin/python scripts/scrape_google_images.py --query "OTR On The Run fuel price sign Adelaide South Australia" --brand otr --max 30 &
.venv/bin/python scripts/scrape_google_images.py --query "Liberty fuel price sign Melbourne Victoria Australia" --brand liberty --max 30 &
wait
```

### 2. Convert formats before ingest

```bash
# Convert PNGs to JPEG (required for labeling agents)
find data/ingest/ -name '*.png' | while read f; do
  sips -s format jpeg "$f" --out "${f%.png}.jpg" 2>/dev/null && rm "$f"
done
```

### 3. Run ingest pipeline

```bash
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py
```

### 4. Launch labeling agents

After ingest, go straight to Sonnet labeling in batches of 5 images:
- Max 5 Sonnet agents concurrent (tested safe at 5 in production)
- Each agent screens + labels in one pass
- Expected yield: 25-40% from Bing scrapes, 40-100% from state+brand queries

### 5. Reconcile after labeling

```bash
# Reconcile manifest vs annotation files
.venv/bin/python -c "
import json, os, csv
manifest = 'data/tmp/labeling_manifest.csv'
with open(manifest) as f: lines = f.readlines()
from datetime import datetime, timezone
ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
fixed = 0
for fn in sorted(os.listdir('data/tmp/annotations')):
    if not fn.endswith('.json'): continue
    d = json.load(open(f'data/tmp/annotations/{fn}'))
    if 'sign' not in d: continue
    fname = fn[:-5] + '.jpg'
    brand = d['sign'].get('brand', 'unknown')
    stype = d['sign'].get('sign_type', 'led')
    entries = len(d.get('entries', []))
    for i, line in enumerate(lines):
        if line.startswith(fname + ',') and ',done,' not in line:
            lines[i] = f'{fname},done,yes,{brand},{stype},{entries},B,recovered,{ts}\n'
            fixed += 1
            break
with open(manifest, 'w') as f: f.writelines(lines)
print(f'Fixed {fixed} rows')
"

# Clean skip-annotation pollution
for f in data/tmp/annotations/*.json; do
  python3 -c "import json; d=json.load(open('$f')); 'sign' not in d and exit(1)" 2>/dev/null || rm -f "$f"
done
```

---

## GitHub Copilot Agent Dispatch (Alternative)

For large-scale scraping, dispatch to GitHub Copilot SWE agents:

```bash
gh agent-task create --custom-agent scraper "<TASK DESCRIPTION>"
```

See `docs/prompts/scrape_fuel_signs_v5.md` for the agent prompt template.

**Completed tasks (do NOT re-run):**

| Task | PR | Result | Date |
|------|-----|--------|------|
| Wikimedia deep scrape (all states, all brands) | #22 | 97 scraped, 9 new after dedup | 2026-04-04 |
| Flickr fuel station photographers batch | — | 31 images, high quality | 2026-04-09 |
| State+brand Wikimedia sweep | — | 31 images | 2026-04-09 |
| Mainstream brands suburban AU | — | 28 images | 2026-04-09 |
| News sources (Costco/Metro/night) | — | 14 images | 2026-04-09 |
| Bing: EG, Apco, Puma, OTR, Metro, United, Liberty, Costco | — | 70 new (deduped), ~16 labeled | 2026-04-11 |

**Key findings:**
- Wikimedia is ~90% exhausted for AU fuel stations
- YouTube thumbnails ~5% useful
- Bing generic brand queries: 23% overall yield (poor)
- Bing state+brand queries: 40-100% yield (excellent)

---

## Scaling Estimates

Based on observed yields:

| Strategy | Scrape:Dedup:Label ratio | To get 30 labels |
|----------|-------------------------|-------------------|
| State+brand Bing | 30 scraped → 20 new → 10 labeled | ~90 scraped |
| Generic brand Bing | 30 scraped → 10 new → 3 labeled | ~300 scraped |
| Wikimedia (exhausted) | Diminishing returns | Not recommended |
| Flickr photographers | High quality but finite pool | ~60 scraped |
| News articles | 30 scraped → 15 new → 5 labeled | ~180 scraped |

**Rule of thumb:** Plan 3x the scrape volume you think you need, because dedup + quality screening removes 60-75%.
