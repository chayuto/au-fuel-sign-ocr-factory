---
name: scrape-dispatch
description: |
  Dispatches scrape tasks to GitHub Copilot agents for parallel image collection.
  Each task targets a unique source+query combination to avoid duplicates across agents.
  Use this skill when the user wants to "scrape more", "collect images", "dispatch scraper",
  "launch scrape agents", or "fill brand gaps".
---

# Scrape Dispatch: Launch GitHub Copilot Scrape Agents

## How It Works

Each scrape task is dispatched to GitHub's Copilot SWE agent via `gh agent-task create`.
The agent runs in a cloud VM, scrapes images, commits to a branch, and opens a PR for review.

**Key principle: each task has a unique, non-overlapping scope** (source + target + query)
so multiple agents can run in parallel without duplicating work.

## Task Registry

Before dispatching, check what's already running or completed:

```bash
# List active/recent scrape tasks
gh agent-task list | head -20

# List open scrape PRs
gh pr list --state open --search "scrape" --json number,title,createdAt

# List recently merged scrape PRs
gh pr list --state merged --search "scrape" --limit 10 --json number,title,mergedAt
```

## Dispatching a Task

Each task must specify a unique **source + target + search strings**:

```bash
gh agent-task create --custom-agent scraper "<TASK DESCRIPTION>"
```

### Task Description Template

```
Scrape Australian fuel station price sign images.

SOURCE: <Wikimedia Commons | YouTube thumbnails | News site>
TARGET: <brand or category>
SEARCH STRINGS:
- "<query 1>"
- "<query 2>"
- "<query 3>"

WIKIMEDIA CATEGORIES (if applicable):
- Category:<name>

EXPECTED YIELD: <low/medium/high>
PRIORITY: <critical/high/medium>

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.
```

## Completed Tasks (do NOT re-run)

| Task | PR | Result | Date |
|------|-----|--------|------|
| Wikimedia deep scrape (all states, all brands) | #22 | 97 scraped, 9 new after dedup | 2026-04-04 |
| Costco YouTube thumbnails | #23 | in progress | 2026-04-04 |
| Metro+OTR news articles | #24 | in progress | 2026-04-04 |
| Night/dusk Wikimedia | #25 | in progress | 2026-04-04 |
| v4 slots 1-8 (Wiki, YT, news, blogs) | #9-17 | 87 new images | 2026-04-03 |
| v4 slots 9,11 (forums, brand sites) | #19-20 | 23 images, mostly rejected | 2026-04-03 |

### Key findings
- **Costco + Metro have ZERO Wikimedia images** — must use news/YouTube/web
- **Wikimedia is ~90% exhausted** — v5 deep scrape got only 9 new from 97 downloaded
- **YouTube thumbnails are ~5% useful** — most are talking heads or memes
- **News composites must be filtered** — only save direct station photos

## Pre-Built Task Catalog

Check the completed table above first. Do NOT re-run completed tasks.

### CRITICAL — Costco (have 0, NOT on Wikimedia)

**Task C1: Wikimedia Costco** — COMPLETED (zero yield, Costco not on Wikimedia)

~~**Task C2: YouTube Costco**~~ — DISPATCHED as #23

**Task C3: News Costco**
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: News articles — extract ONLY direct station photos, reject composites
TARGET: Costco fuel stations in Australia (Docklands VIC, Auburn NSW, Epping VIC, Casula NSW, Marsden Park NSW, Canberra ACT)
SEARCH STRINGS:
- "Costco fuel" price sign site:9news.com.au
- "Costco petrol" price board site:7news.com.au
- "Costco fuel" station site:abc.net.au
- "Costco fuel" price site:news.com.au
- "Costco fuel" queue price sign Australia 2024 2025 2026
- "Costco fuel" Docklands OR Auburn OR Epping photo
EXPECTED YIELD: low-medium (news is the best remaining source for Costco)
PRIORITY: critical

Costco has ZERO images on Wikimedia and ZERO from YouTube thumbnails.
News articles with fuel price stories are the best remaining source.
Only save DIRECT station photographs — reject composites, charts, portraits.

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

~~**Task C2: YouTube Costco (retry with strict filter)**~~ — DISPATCHED as #23
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: YouTube thumbnails
TARGET: Costco fuel stations — ONLY save if a physical price sign board with readable LED prices is clearly visible in the thumbnail
SEARCH STRINGS:
- "Costco fuel Australia price"
- "Costco petrol station price board"
- "cheapest fuel Costco Australia 2025 2026"
EXPECTED YIELD: low (v4 got 0/10 usable — most thumbnails are talking heads)
PRIORITY: critical

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### OTR (have ~7 after v5) — Wikimedia covered by #22

**Task O1: Wikimedia OTR** — COVERED by #22 (got 14 OTR, ~5 new after dedup)
~~**Task O1+M1 news:**~~ — DISPATCHED as #24
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: OTR (On The Run) fuel stations in South Australia
SEARCH STRINGS:
- "On The Run fuel"
- "OTR fuel station"
- "OTR petrol Adelaide"
WIKIMEDIA CATEGORIES:
- Category:On_The_Run_(convenience_stores)
- Category:Petrol_stations_in_South_Australia
EXPECTED YIELD: medium
PRIORITY: critical

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### Metro (have 2) — NOT on Wikimedia, covered by news task #24

**Task M1: Wikimedia Metro** — SKIP (zero on Wikimedia, confirmed by #22)
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: Metro Petroleum stations
SEARCH STRINGS:
- "Metro Petroleum"
- "Metro Petroleum price"
- "Metro fuel station"
WIKIMEDIA CATEGORIES:
- Category:Petrol_stations_in_New_South_Wales (filter for Metro)
- Category:Petrol_stations_in_Victoria (filter for Metro)
EXPECTED YIELD: low-medium
PRIORITY: critical

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### Liberty (have ~7) — Wikimedia covered by #22

**Task L1: Wikimedia Liberty** — COVERED by #22 (got 5 Liberty, ~2 new after dedup)
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: Liberty Oil fuel stations
SEARCH STRINGS:
- "Liberty Oil" Australia
- "Liberty fuel" station
- "Liberty petrol"
WIKIMEDIA CATEGORIES:
- Category:Liberty_Oil
- Category:Petrol_stations_in_Western_Australia (filter for Liberty)
EXPECTED YIELD: low-medium
PRIORITY: high

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### Night/dusk shots (have ~15%, need 30%)

~~**Task N1: Wikimedia night stations**~~ — DISPATCHED as #25
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: Night/dusk/evening fuel station photos (any brand)
SEARCH STRINGS:
- "petrol station night" Australia
- "fuel station dusk" Australia
- "servo night" Australia
- "service station evening" Australia
WIKIMEDIA CATEGORIES:
- Category:Night_photographs_in_Australia (filter for fuel/petrol/servo)
EXPECTED YIELD: low-medium
PRIORITY: high

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### MEDIUM — 7-Eleven (have 7)

**Task S1: Wikimedia 7-Eleven**
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: 7-Eleven fuel stations in Australia
SEARCH STRINGS:
- "7-Eleven fuel Australia"
- "7-Eleven petrol station"
WIKIMEDIA CATEGORIES:
- Category:7-Eleven_in_Australia
EXPECTED YIELD: medium
PRIORITY: medium

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

### VOLUME — Wikimedia state sweep

**Task W1: Wikimedia QLD** (Puma territory)
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: All fuel stations in Queensland
SEARCH STRINGS:
- "petrol station Queensland"
- "fuel price" Queensland
WIKIMEDIA CATEGORIES:
- Category:Petrol_stations_in_Queensland (crawl ALL files)
EXPECTED YIELD: medium-high
PRIORITY: medium

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

**Task W2: Wikimedia WA** (Liberty/independent territory)
```bash
gh agent-task create --custom-agent scraper 'Scrape Australian fuel station price sign images.

SOURCE: Wikimedia Commons
TARGET: All fuel stations in Western Australia
SEARCH STRINGS:
- "petrol station Western Australia"
- "fuel price" "Western Australia"
WIKIMEDIA CATEGORIES:
- Category:Petrol_stations_in_Western_Australia (crawl ALL files)
EXPECTED YIELD: medium
PRIORITY: medium

Follow all quality rules in docs/prompts/scrape_fuel_signs_v5.md.
Write ONLY to data/ingest/batch_<UTC>/. Do NOT scrape anything outside the scope above.'
```

## After Dispatching

1. Note which tasks you launched (IDs and targets)
2. Check back with `gh agent-task list` for completion
3. Review the PRs — check image count and scrape_report.md
4. Merge good PRs, close empty/bad ones
5. Run `data-pipeline` skill to process ingest → screen → label

## Adding New Tasks

When creating a new task not in the catalog:
1. Pick a unique source + target + query combination
2. Check it doesn't overlap with existing/completed tasks
3. Use the template above
4. Keep scope narrow — one source, one brand/category per task
