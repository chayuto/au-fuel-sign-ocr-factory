---
name: scrape-dispatch
description: |
  Plans and executes scrape campaigns for Australian fuel station price sign images.
  Assesses current dataset state, brand gaps, and historical yield.
  Use this skill when the user wants to "scrape more" or "collect images".
---

# Scrape Dispatch: Plan & Execute (Gemini Way)

## Step 0: Assess Before Scraping

**Never scrape blind.** Before planning queries:

### 0a. Check current counts
Run a Python script to count brands in `data/tmp/annotations/*.json` and manifest status.

### 0b. Identify brand gaps
Prioritize brands with the largest gaps to targets (50+ for majors, 25+ for medium, 15+ for minor).
Gap = Target - Current count.

### 0c. Review yield
Check skip vs. label ratios in `data/tmp/pipeline_events.jsonl`.

---

## Campaign Strategy: Always Winners + Variance

**RULE: ~60% proven winners + ~40% new experimental queries.**

### Tier 0: Proven Winners
- `"APCO fuel price sign {City} Victoria"`
- `"EG Foodary fuel price pylon {City} Australia"`
- `"petrol price war Australia sign board cheap fuel"`

### Tier 1: State+Brand (USE FIRST)
Template: `"{Brand} fuel price sign {City/Suburb} {State} Australia"`
**Higher yield:** Wodonga/Bendigo (APCO), Gregory Hills (EG), Bankstown (Metro), Rockhampton (Puma).

### Tier 2: News + Location
Template: `"fuel price {brand} {city} site:{news_domain}"`
(e.g., Canberra Times, Adelaide Now).

---

## Running a Scrape Campaign

### 1. Plan queries
Target the biggest gaps using state+brand templates.

### 2. Execute scrape
```bash
python scripts/scrape_google_images.py --query "{query}" --brand {brand} --max {count}
```

### 3. Run ingest pipeline
```bash
.venv/bin/python .claude/skills/data-pipeline/scripts/process_ingest.py
```

### 4. Proceed to labeling
Once ingested to `data/tmp/`, proceed to `fuel-sign-labeler`.
