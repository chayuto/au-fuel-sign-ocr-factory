# Agent Prompt: Search Kaggle & Open Images for Fuel Sign Data

## Objective
Search Kaggle and Google Open Images for fuel price sign / petrol station datasets.

## Search Queries
- "fuel price sign dataset"
- "gas station price board kaggle"
- "petrol station sign recognition"
- "fuel price OCR dataset"
- "gas price display detection"

## Steps

1. **Web Search**: Use WebSearch to find datasets on Kaggle and Open Images.
2. **Inspect Pages**: For each result, use WebFetch to check:
   - Image count, format, labels/annotations
   - Download size, license
   - Whether it includes bounding box annotations or just images
3. **Visual Validation (HARD REQUIREMENT)**: Download at least one sample image to `/tmp/kaggle_sample_*.jpg` using Bash. Use the Read tool to actually view the image and confirm it shows fuel price signs with readable prices.
   - If you CANNOT visually validate any image, mark as UNVERIFIED.
4. **Report**: Write to `/tmp/kaggle_search_results.md`:
   - Dataset name, URL, size, format, labels
   - Visual validation status
   - Suitability for Australian fuel sign OCR

## Failure Condition
If no datasets found or none visually validated → TASK FAILED with explanation.
