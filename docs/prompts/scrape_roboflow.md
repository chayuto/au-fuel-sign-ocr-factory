# Agent Prompt: Scrape Roboflow for Fuel Sign Datasets

## Objective
Search Roboflow Universe for existing fuel price sign / petrol station price board datasets suitable for training an Australian fuel sign OCR model.

## Search Queries
- "fuel price sign"
- "petrol station board"
- "gas station price"
- "fuel board detection"
- "fuel price display"
- "petrol price"

## Steps

1. **Web Search**: Use WebSearch to find Roboflow Universe datasets matching the queries above.
2. **Inspect Dataset Pages**: For each promising result, use WebFetch on the dataset URL to extract:
   - Total image count
   - Annotation format (YOLO, COCO, VOC, etc.)
   - Class/label names
   - License
   - Preview image URLs
3. **Visual Validation (HARD REQUIREMENT)**: Download at least one sample image from each promising dataset to `/tmp/roboflow_sample_*.jpg` using Bash (curl/wget). Then use the Read tool to view the image. Confirm:
   - Image actually shows a fuel/petrol price sign
   - Prices are legible
   - Annotations (if visible) align with sign regions
   - If you CANNOT visually validate, mark the dataset as UNVERIFIED and explain why.
4. **Report**: Write results to `/tmp/roboflow_search_results.md` with:
   - Dataset name, URL, image count, format, classes, license
   - Visual validation status (VERIFIED / UNVERIFIED)
   - Suitability rating (HIGH / MEDIUM / LOW) for Australian fuel sign OCR
   - Screenshot/sample description

## Failure Condition
If no datasets can be found or none can be visually validated, explicitly state TASK FAILED with reasons.
