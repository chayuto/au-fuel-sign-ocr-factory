---
name: fuel-sign-labeler
description: |
  Multimodal labeling agent for Australian fuel station price sign images. Uses Claude's vision to
  look at each image, classify whether it contains a visible fuel price sign board, and if so,
  produce YOLO bounding box annotations + JSON sidecar metadata following the project's 4-class
  Finder schema (sign_board, brand_zone, fuel_label, fuel_price). Manages a labeling_manifest.csv
  to track progress and prevent duplicate work across concurrent agents. Use this skill whenever
  the user wants to label, annotate, or tag fuel sign images for training, or when they want to
  launch labeling agents on a batch of images. Also trigger when the user mentions "label",
  "annotate", "bbox", "bounding box", or "YOLO labels" in the context of fuel sign images.
---

# Fuel Sign Labeler

## Prompt Versioning

Every labeling run must record which prompt version was used. This lets us track
quality regressions and attribute annotations to specific prompt logic.

**Current version: v5** (2026-04-08)

| Version | Date | Key Changes | Annotations | Quality Notes |
|---------|------|-------------|-------------|---------------|
| v1 | 2026-03-29 | Initial blind estimation, no VQA | ~149 | Every annotation had errors (EXP-001) |
| v2 | 2026-03-30 | Added visual QA (preview + verify) | ~149 relabeled | +56% mAP vs v1 (EXP-002) |
| v3 | 2026-04-03 | Added Haiku screening gate, skip criteria | ~30 | 71-88% unusable filtered cheaply |
| v4 | 2026-04-04 | Hardened screening: reject composites, pump displays, close-ups, ≥15% size | ~24 | Caught pump displays, news composites |
| v5 | 2026-04-08 | Tightened sign_board scope (fuel rows only), quality checklist, Sonnet second-pass gate, max 2 concurrent | ~92 in progress | Explicit "NOT brand logos/promo/pylon" rule |

**When updating the prompt:** Increment the version, add a row to this table, and note the
change in the labeling log via `--agent sonnet_v{N}_{batch}`.

### Benchmark Protocol

After each labeling run, measure quality on a random sample:

```bash
# 1. Pick 10 random new annotations
ls data/tmp/annotations/gimg_*.json | perl -MList::Util=shuffle -e 'print shuffle(<>)' | head -10

# 2. Visually inspect each preview — score on 5 criteria:
#    a) sign_board tight on fuel rows only? (not brand/promo/pylon)
#    b) fuel_label/price bboxes correctly paired and aligned?
#    c) all bboxes inside sign_board?
#    d) correct brand, fuel types, prices?
#    e) natural Australian camera frame? (not composite/stock/foreign)
#
# Score: GOOD (all 5 pass) / OK (4 pass) / BAD (≤3 pass)

# 3. Record results in docs/experiments/ or labeling_log
```

**Quality targets by prompt version:**
- v1-v2: no benchmark (retroactive)
- v3-v4: ~70% GOOD, ~20% OK, ~10% BAD
- v5+: target **≥80% GOOD**, ≤15% OK, ≤5% BAD

If BAD rate exceeds 10%, stop labeling and fix the prompt before continuing.

## Workflow: Direct Sonnet Labeling (v5+)

**UPDATE (2026-04-08):** The two-phase Haiku→Sonnet workflow has been RETIRED.

**Why Haiku screening was dropped:**
- Haiku agents given 300+ images take shortcuts — they use filename heuristics instead
  of actually looking at images. Two agents screened 630 images and rejected only 2 (99.7%
  pass rate), when the real reject rate from Sonnet is ~60-70%.
- Haiku can't do quality screening at scale. It's too cheap/fast and optimizes for throughput
  over accuracy.
- The cost savings were illusory — Sonnet's second-pass gate catches everything Haiku would
  catch, plus subtle issues Haiku misses.

**Current workflow: Sonnet labels directly in batches of 5.**

Each Sonnet agent:
1. Reads each image (vision)
2. Classifies HAS_SIGN yes/no (second-pass gate — replaces Haiku screening)
3. If yes: annotates with full bboxes + visual QA
4. If no: skips — **update manifest ONLY, do NOT write annotation JSON for skips**

This is simpler, more reliable, and produces ~30-40% labeled yield. The skip step
IS the screening — built into the labeling agent, not a separate phase.

**Concurrency:** Max 2 Sonnet agents OR 3-5 Opus agents. More than that → 529 overload.

**Batch size:** 5 images per agent. Larger batches (10+) reduce quality as agents rush.

**Agent prompt must include these rules:**
1. Images are at `data/tmp/{filename}` (NOT `data/tmp/images/`)
2. Only write annotation JSON + YOLO label + preview for LABELED images
3. For skipped images: do NOT create files in annotations/
4. Read prompt version from `configs/prompt_version.json` and include in every JSON sidecar
5. Agent name must include version: `sonnet_v5_{batch}` or `opus_v5_{batch}`
6. **MANDATORY LOGGING** — after EACH image, log the event:

For labeled images:
```bash
.venv/bin/python scripts/pipeline_logger.py log \
    --image {filename} --stage label --agent {agent_id} \
    --model {sonnet|opus} --prompt-version v5 --action labeled \
    --brand {brand} --entries {n} --quality {q}
```

For skipped images:
```bash
.venv/bin/python scripts/pipeline_logger.py log \
    --image {filename} --stage label --agent {agent_id} \
    --model {sonnet|opus} --prompt-version v5 --action skipped \
    --reason "{brief reason}"
```

7. At end of batch, report summary with challenges/feedback

**After every labeling run**, the orchestrator MUST:
1. Reconcile manifest against annotation files on disk:
   ```bash
   python scripts/audit_dataset.py --full
   ```
2. Remove any skip-annotation files (no `sign` key) from annotations/
3. Generate run report:
   ```bash
   python scripts/pipeline_logger.py report --agent {agent_id}
   ```

### RETIRED: Phase 1 Haiku Screening

> **Do NOT use Haiku screening for batches > 20 images.** It will shortcut to heuristics.
> For small targeted batches (≤20 images), Haiku screening is still OK as a quick filter
> before manual review, but it should NOT be the only quality gate.

Original Phase 1 prompt (kept for reference only):

#### Old Phase 1: Haiku Screening (RETIRED for large batches)

**Model:** `haiku` — good enough for binary "has sign?" classification.

**Concurrency:** Up to **10 parallel agents** (Haiku is lighter on rate limits).

**Performance:** ~10-20s per image, ~3-5K tokens. Very cheap.

**What it does:** Read image → classify HAS_SIGN yes/no → update manifest (skip or keep-for-labeling) → log.

**Launch pattern:**
```
Agent(
  model: "haiku",
  description: "Screen {image_stem}",
  prompt: "You are a screening agent. Look at ONE image: `{filename}`\n\n[screening prompt]",
  run_in_background: true,
)
```

Launch up to 8-10 at a time. Images that pass screening get queued for Phase 2.

**Important:** Have agents read the manifest directly to get filenames — do NOT pass filenames
via the prompt (they get out of sync due to process_ingest renaming). Also convert ALL non-JPEG
files (webp, avif, png) to JPEG before screening — Haiku cannot read non-JPEG formats.

### Phase 2: Sonnet Labeling (quality, sequential)

**Model:** `sonnet` — needed for accurate bbox estimation, price reading, and visual QA.

**Concurrency:** Max **2 parallel agents**. 8 parallel Sonnet agents causes 529 API overload.
Each agent handles ~46 images. Quality over speed — each image needs full visual QA.

**Learned the hard way:** 8 parallel Sonnet agents all hit 529 overload and produced zero results.
2 agents is the safe maximum for sustained labeling runs.

**Performance:** ~300s per image, ~45K tokens.

**What it does:** Full annotation pipeline — bboxes, metadata, validation, preview, visual QA.

**Launch pattern:**
```
Agent(
  model: "sonnet",
  description: "Label {image_stem}",
  prompt: "You are a labeling agent. Label ONE image: `{filename}`\n\n[full labeling prompt]",
  run_in_background: true,
)
```

### When to use each phase

| Scenario | Phase |
|----------|-------|
| **Any new pending images** | **Phase 1 first, always.** Then Phase 2 on keepers. |
| Re-labeling existing done annotations with VQA | Phase 2 only (already classified) |

**Rule: Every new image must pass Haiku screening before Sonnet labeling.**
No exceptions, even for "targeted scrapes" — scrape agents sometimes download station
exteriors, canopy shots, or heritage photos without price signs. Haiku catches these
cheaply (~3s each) instead of wasting Sonnet time (~300s each).

---

## Scope

**This skill is for IMAGE LABELING only.** Your job is to annotate images that already exist in `data/tmp/`.

You do NOT:
- Download, scrape, or fetch new images from the web
- Write to `data/ingest/` — that is the scrape staging area
- Run training, export, or dataset build scripts
- Modify code, configs, or docs

---

## Phase 1: Haiku Screening Prompt

Use this prompt when launching Haiku screening agents. Each agent screens one image.

```
You are a screening agent. Look at ONE image and decide: does it contain a visible
Australian fuel station price sign board with at least one readable price?

Image: `data/tmp/{filename}`

Step 1: Read the image using the Read tool.

Step 2: Classify:
  HAS_SIGN = yes if ALL true:
  - A fuel price sign/board is visible (pylon, canopy fascia, or wall panel)
  - At least one fuel type label is readable ("Unleaded", "Diesel", "E10", etc.)
  - At least one price is readable (XXX.X format, LED or printed digits)
  - Sign occupies ≥15% of image area (not a distant shot)
  - Image is a NATURAL CAMERA FRAME (a real photo, not a composite or screenshot)

  HAS_SIGN = no if ANY true:
  - No fuel price sign visible (just pumps, canopy, building, road)
  - Sign too distant/tiny to read (<15% of image area)
  - Prices blank/off or placeholder (999.9, 000.0)
  - >70% occluded
  - Historical/heritage with no readable modern price board
  - **Pump/bowser transaction display** — a pump LCD showing litres/dollars/price-per-litre
    for an active fill. These are NOT price sign boards. Skip them.
  - Product shot of LED digits without station context
  - **News composite / editorial image** — sign is pasted next to unrelated content
    (explosion, portrait, map, chart, pump nozzle collage). If the image is clearly
    NOT a single camera photo of a station, skip it.
  - **Extreme close-up crop** — image is tightly cropped to just the price digits with
    no surrounding sign structure or station context visible. Real camera frames
    always include context.
  - **Screenshot of an app, website, or article** — not a direct photo of a sign

Step 3: Update manifest.
  Read data/tmp/labeling_manifest.csv, find the row for {filename}.
  - If HAS_SIGN = no: set status to "skipped", write file back.
  - If HAS_SIGN = yes: leave as "pending" (Sonnet will label it later).

Step 4: Log the result.
  If skipped:
    .venv/bin/python scripts/labeling_log.py append \
      --file {filename} --action skipped --agent haiku_screen_{N} \
      --reason "brief reason"

  If has sign (no log needed — Sonnet will log when labeling):
    Just report: "HAS_SIGN=yes, ready for Sonnet labeling"

That's it. Do NOT annotate, do NOT write bboxes, do NOT generate previews.
Just screen and skip/keep.
```

---

## Phase 2: Sonnet Labeling (Full Annotation)

You are a multimodal labeling agent for Australian fuel station price sign images. Your job is to look at each image, decide if it contains a usable fuel price sign, and produce structured annotations for YOLO object detection training.

**The most important rule: you must VISUALLY VERIFY every annotation.** After writing bboxes, you generate a preview image with boxes drawn on it, then READ that preview to confirm the boxes actually land on the right elements. If they don't, you fix them. Never mark an image as done without seeing the preview.

## How it works

For each image you:
1. **Read** the image (Claude can see images via the Read tool)
2. **Classify** — does it contain a fuel price sign with readable prices?
3. **Annotate** — if yes, estimate bounding boxes and extract metadata
4. **Write** — output YOLO label file + JSON sidecar
5. **Validate** — run `validate_annotations.py` to catch structural/domain errors, fix if any
6. **Preview & Verify** — generate preview, READ it, confirm boxes are correct, fix if not
7. **Track** — update the manifest CSV and labeling log

## Step 0: Setup

Before processing any images, ensure the output directories exist:

```bash
mkdir -p data/tmp/labels data/tmp/annotations data/tmp/preview
```

Read the manifest to find your batch. The manifest is at `data/tmp/labeling_manifest.csv`. Only process rows where `status` is `pending`.

**Batch assignment:** When the user launches you, they'll specify a batch — either a filename prefix pattern (e.g., `wiki_ampol_*`), a line range (e.g., lines 100-150), or an explicit file list. Process only your assigned batch to avoid conflicts with other agents.

## Step 1: Read and classify each image (SECOND-PASS GATE)

Even though Haiku screening already passed this image, YOU must re-classify it.
Haiku makes false positives. **If the image is bad, SKIP it — do not force an annotation.**

Use the Read tool to view the image file. Then make a binary decision:

**HAS_SIGN = yes** if ALL of these are true:
- A fuel price sign/board is visible (pylon, canopy fascia, or wall-mounted)
- At least one fuel type label is readable (e.g., "Unleaded", "Diesel", "E10")
- At least one price is readable (LED digits or printed numbers showing XXX.X format)
- The sign occupies ≥15% of image area
- Image is a natural camera frame (not a composite, screenshot, or editorial crop)

**HAS_SIGN = no** (skip) if ANY of these:
- No fuel price sign visible (just pumps, canopy, building, road)
- Sign is too distant/tiny to read any text or prices (<15% of image)
- All prices are blank/off (LEDs not illuminated) or placeholder (999.9, 000.0)
- Sign is >70% occluded by trees, poles, or other objects
- Image is a historical photo (pre-1990s) with no readable price board
- **Pump/bowser transaction display** — pump LCD showing litres/dollars during a fill, NOT a price sign
- Image is a product shot of LED digits without station context
- **News composite / editorial image** — sign pasted next to unrelated content (not a single camera photo)
- **Extreme close-up crop** — only price digits visible, no sign structure or station context
- **Screenshot of app, website, or article** — not a direct photo

## Step 2: Annotate (if HAS_SIGN = yes)

### 2a: Identify metadata

From the image, determine:
- **brand**: Match to a key from `configs/brands.yaml`: `shell`, `bp`, `ampol`, `caltex`, `seven_eleven`, `united`, `costco`, `liberty`, `puma`, `metro`, `mobil`, `otr`, `independent`
- **sign_type**: `led` (most common — glowing digits), `mechanical` (flip digits), `backlit` (printed panel with backlight), `digital` (LCD screen)
- **time_of_day**: `day`, `night`, `dusk`
- **weather**: `clear`, `overcast`, `rain`

### 2b: Estimate bounding boxes

You'll estimate normalized [0,1] coordinates for each detection. Think of the image as a 1.0 x 1.0 grid where (0,0) is top-left and (1,1) is bottom-right.

The coordinate system uses `[x1, y1, x2, y2]` (top-left corner to bottom-right corner), which gets converted to YOLO format `cx cy w h` for the label file.

**How to estimate well — use reference points:**

1. Start with the **sign_board**. This is ONLY the rectangular area containing fuel type rows and price rows. **Do NOT include:**
   - Brand logos (BP, Caltex, OTR, Shell) — that's brand_zone
   - Promo banners (COFFEE, SUBWAY, Vortex, loyalty cards)
   - Pylon pole or structural elements
   The sign_board top edge should be at or just above the FIRST fuel row. The bottom edge at or just below the LAST fuel row. For example: "the price panel starts at about 30% from the left and 40% from the top, extends to 70% right and 85% down" → `[0.30, 0.40, 0.70, 0.85]`.

2. For each **fuel row**, locate it WITHIN the sign_board area:
   - The fuel label text (e.g., "Unleaded") is on the left portion of the sign
   - The price digits (e.g., "209.7") are on the right portion of the sign
   - Each row occupies a horizontal band at a specific vertical position
   - Rows are evenly spaced vertically

3. **Sanity checks before writing:**
   - All fuel_label and fuel_price bboxes must fall INSIDE the sign_board bbox
   - fuel_label must be LEFT of fuel_price (label.x2 < price.x1)
   - Paired label and price must be at the same Y-position (similar y1, y2)
   - Each bbox should tightly wrap its content — not too loose, not overlapping neighbors

**What to annotate (4 classes from `configs/finder_classes.yaml`):**

| class_id | Name | What | How many |
|----------|------|------|----------|
| 0 | `sign_board` | The rectangular price panel (all fuel rows). Exclude brand logo, promo banners, pylon pole. | Exactly 1 |
| 1 | `brand_zone` | Brand logo + name area at top of pylon. Omit if not visible. | 0 or 1 |
| 2 | `fuel_label` | Each fuel type text label. One per visible fuel row. | 1-8 |
| 3 | `fuel_price` | Each LED/printed price display. One per visible fuel row. Must pair 1:1 with labels. | 1-8 |

**Critical pairing rule:** Every `fuel_label` needs a matching `fuel_price` at the same Y-position. If a row's price is unreadable or blank, skip that row entirely (don't annotate either the label or price).

### 2c: Read the text and prices

For each fuel row, record:
- **display_text**: Exact text on the sign (e.g., "Unleaded E10", "V-Power", "Ultimate Diesel")
- **fuel_type**: Map to canonical ID from `configs/fuel_types.yaml`: `U91`, `E10`, `P95`, `P98`, `Diesel`, `LPG`, `AdBlue`, `E85`
- **price**: The numeric value in cents per litre (e.g., `189.9`). Australian prices are almost always `XXX.X` format.

Mapping hints:
- "Unleaded" / "Unleaded 91" / "Regular" / "ULP" → `U91`
- "Unleaded E10" / "E10" / "Ethanol" → `E10`
- "Premium 95" / "95" → `P95`
- "Premium 98" / "V-Power" / "Ultimate 98" / "Vortex 98" → `P98`
- "Diesel" / "Ultimate Diesel" / "Vortex Diesel" / "DSL" → `Diesel`
- "LPG" / "Autogas" → `LPG`

## Step 3: Write outputs

### YOLO label file

Write to `data/tmp/labels/{stem}.txt` where `{stem}` is the filename without extension.

Format: one line per detection, `class_id cx cy w h` (all normalized [0,1]).

Convert from `[x1, y1, x2, y2]` to YOLO center format:
- `cx = (x1 + x2) / 2`
- `cy = (y1 + y2) / 2`
- `w = x2 - x1`
- `h = y2 - y1`

Example for a sign with 3 fuel rows:
```
0 0.500000 0.650000 0.700000 0.450000
1 0.500000 0.150000 0.700000 0.200000
2 0.300000 0.480000 0.250000 0.060000
3 0.700000 0.480000 0.250000 0.060000
2 0.300000 0.580000 0.250000 0.060000
3 0.700000 0.580000 0.250000 0.060000
2 0.300000 0.680000 0.250000 0.060000
3 0.700000 0.680000 0.250000 0.060000
```

### JSON sidecar

Write to `data/tmp/annotations/{stem}.json`. Follow the `FuelSignAnnotation.to_dict()` format from `schema.py`:

```json
{
  "prompt_version": "v5",
  "image": {
    "file": "example.jpg",
    "source": "web",
    "conditions": {
      "time_of_day": "day",
      "weather": "clear"
    }
  },
  "sign": {
    "bbox": [0.15, 0.42, 0.85, 0.88],
    "brand": "shell",
    "sign_type": "led",
    "brand_bbox": [0.15, 0.05, 0.85, 0.25]
  },
  "entries": [
    {
      "fuel_type": "E10",
      "display_text": "Unleaded E10",
      "price": 139.9,
      "label_bbox": [0.16, 0.45, 0.42, 0.51],
      "price_bbox": [0.58, 0.45, 0.84, 0.51]
    },
    {
      "fuel_type": "U91",
      "display_text": "Unleaded",
      "price": 141.4,
      "label_bbox": [0.16, 0.53, 0.42, 0.59],
      "price_bbox": [0.58, 0.53, 0.84, 0.59]
    }
  ]
}
```

## Step 4: Validate (MANDATORY)

Run the structural validator immediately after writing the JSON and YOLO files:

```bash
.venv/bin/python scripts/validate_annotations.py data/tmp/annotations/{stem}.json
```

This checks:
- Only 1 sign_board, max 8 entries (warn >6)
- All bboxes inside [0,1] range with valid dimensions
- Brand, fuel_type, sign_type are valid enum values
- Price in expected range (80-350 cpl, 40-150 for LPG)
- All label/price bboxes inside sign_board
- Label LEFT of price, same Y-position per row
- No duplicate rows (same Y-center)

**If the validator reports any ERRORs, fix them before proceeding to Step 5.** Warnings are OK to proceed with but worth double-checking.

## Step 5: Preview & Verify (MANDATORY)

This is the most important step. You must visually confirm your boxes are correct.

### 5a: Generate the preview

```bash
.venv/bin/python scripts/draw_annotations.py --files {stem}
```

This draws color-coded bounding boxes on the image:
- **Green** = sign_board
- **Orange** = brand_zone
- **Cyan** = fuel_label
- **Red** = fuel_price

It also runs automated checks and prints any issues found.

### 5b: READ the preview image

Use the Read tool to view `data/tmp/preview/{stem}_preview.jpg`. Actually LOOK at it.

**Check these things visually:**
1. Does the **green sign_board box** tightly wrap the price panel area? Not the whole pylon, not the brand logo — just the rows of fuel entries.
2. Does each **red fuel_price box** land exactly on the LED/printed price digits? Not shifted, not covering neighboring rows.
3. Does each **cyan fuel_label box** land on the fuel type text? Not overlapping with the price.
4. Are label and price boxes on the **same horizontal line** for each row?
5. Are ALL label and price boxes **inside** the green sign_board box?

### 5c: Fix if wrong

If ANY box looks wrong in the preview:
1. Re-read the original image
2. Identify which coordinates are off
3. Rewrite the JSON and YOLO label files with corrected coordinates
4. Re-run `draw_annotations.py` to regenerate the preview
5. Re-read the preview to confirm the fix

**Do NOT move on to the next image until the preview looks right.** It is better to have 5 correctly annotated images than 20 with bad boxes.

### Common mistakes to watch for:
- **Boxes shifted** — coordinates estimated from wrong reference point
- **Boxes too large** — covering multiple rows instead of one
- **Label overlapping price** — x2 of label should be < x1 of price
- **Boxes outside sign_board** — all entries must be inside the sign_board bbox
- **Wrong axis on rotated signs** — if the sign is rotated/angled, the rows may not be horizontal in the image. Annotate where they ACTUALLY appear, not where you expect them.

## Step 6: Update the manifest AND labeling log

Only after validation passes AND the preview passes visual inspection, update **both** the manifest and the labeling log.

### 6a: Update the manifest

For **labeled** images:
```
filename,done,yes,<brand>,<sign_type>,<num_entries>,<quality>,sonnet_v5_<batch>,<ISO timestamp>
```

For **skipped** images:
```
filename,skipped,no,,,,<reason>,sonnet_v5_<batch>,<ISO timestamp>
```

Quality ratings:
- `A` — Clear, frontal, high-res, all text readable
- `B` — Usable but some issue (angle, partial occlusion, medium res)
- `C` — Marginal (low res, heavy angle, some text hard to read)

**Important:** When updating the manifest, read the current file, modify only your rows, and write the whole file back. This avoids corrupting other agents' updates.

### 6b: Append to the labeling log

The labeling log (`data/tmp/labeling_log.jsonl`) is the audit trail. Every labeling event gets a line — this is how we track corrections, visual QA coverage, and quality over time. **Always append after every image, whether labeled, skipped, or corrected.**

```bash
# After labeling a new image
.venv/bin/python scripts/labeling_log.py append \
    --file {filename} --action labeled --agent {agent_id} \
    --visual-qa true --brand {brand} --entries {num_entries} --quality {quality}

# After skipping an image
.venv/bin/python scripts/labeling_log.py append \
    --file {filename} --action skipped --agent {agent_id} \
    --reason "{skip reason}"

# After re-labeling / correcting an existing annotation
.venv/bin/python scripts/labeling_log.py append \
    --file {filename} --action corrected --agent {agent_id} \
    --visual-qa true --brand {brand} --entries {num_entries} --quality {quality} \
    --issues-found "{what was wrong, e.g. sign_board too wide, price bbox shifted}"
```

**Actions:**
- `labeled` — first-time annotation of a pending image
- `skipped` — image has no usable fuel sign
- `corrected` — re-labeled an existing annotation and fixed issues (describe what was wrong in `--issues-found`)
- `relabeled` — re-labeled an existing annotation (replacing old blind-estimated labels with visual QA)
- `verified` — reviewed an existing annotation, confirmed it was correct, no changes needed

**Fallback if log file is unavailable:** The script auto-detects when the main log is unwritable (git checked in, locked, permissions, etc.) and writes to `data/tmp/log_fragments/{agent}_{timestamp}.jsonl` instead. The main agent will later run `python scripts/labeling_log.py merge` to fold fragments in. You don't need to handle this — just always run the append command and the script handles the rest.

## Edge cases to handle

These are the tricky situations — read `docs/LABELING_GUIDE.md` for the full guide, but here's the quick version:

- **Promo banners** ("Save 4c", "Velocity"): Not fuel entries. Exclude from sign_board bbox.
- **999.9 / 000.0 prices**: Annotate bboxes normally, add `"placeholder": true` to the JSON.
- **Multiple signs in image**: Annotate only the largest/most prominent one.
- **Product shots** (LED digit modules without station context): Skip — these are for Reader training, not Finder.
- **Historical photos**: Only annotate if a price board with readable text is visible.

## Batch processing tips

- Process images one at a time: Read → classify → annotate → write → validate → preview → verify → fix if needed → manifest → log
- Write outputs immediately after each image — don't batch up writes
- If you encounter an error on one image, log it and move to the next
- Never mark an image as done without viewing the preview
- **Always append to the labeling log** — this is how we track corrections and visual QA coverage

## Quality Philosophy

**There is no point rushing to get garbage data.** One bad annotation in the training set hurts
more than 10 missing images. Every annotation must be trainable quality.

**Skip aggressively.** If you're unsure whether an image is usable, skip it. We can always
scrape more images — we can't easily find and fix bad annotations buried in the dataset.

**Quality checklist before marking "done":**
1. Is this a real Australian fuel station? (not US/UK/Chinese/stock photo)
2. Is the sign_board bbox tight around ONLY the fuel rows? (not brand/promo/pylon)
3. Are ALL fuel_label bboxes LEFT of their paired fuel_price bboxes?
4. Are ALL bboxes INSIDE the sign_board?
5. Did you READ the preview and visually confirm the boxes are correct?
6. Would you trust this annotation to train a model?

If the answer to any of these is "no" or "not sure", either fix it or skip the image.

**10 clean annotations are worth more than 50 sloppy ones.**
