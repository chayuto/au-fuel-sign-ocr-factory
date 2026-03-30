# Agent Prompt: Search News Sites for Fuel Price Sign Images

## Objective
Australian news sites frequently publish articles about fuel prices with photos of fuel price signs. These are a rich source of real-world fuel sign images.

## Target Sites
- ABC News Australia (abc.net.au)
- 9News (9news.com.au)
- News.com.au
- The Guardian Australia
- SBS News
- Drive.com.au
- CarExpert.com.au

## Search Queries
- site:abc.net.au "fuel price" OR "petrol price" photo
- site:9news.com.au "servo" OR "fuel price board"
- "Australian fuel prices" photo 2024 OR 2025 OR 2026
- "petrol station" price sign Australia image
- "fuel price war" Australia photo

## Steps

1. **Web Search**: Search news sites for articles about fuel prices that include photos of price signs.
2. **Inspect Articles**: Use WebFetch on promising articles to find image URLs of fuel price signs.
3. **Download Samples**: Download 3-5 sample images to `/tmp/news_fuel_*.jpg` using Bash.
4. **Visual Validation (HARD REQUIREMENT)**: Use Read to view each downloaded image. For each:
   - Confirm it shows an Australian fuel price sign
   - Note which brand is visible
   - Note which fuel types and prices are legible
   - Note image quality (resolution, angle, lighting)
5. **Licensing Assessment**: Note that news images are typically editorial use only — these serve as reference for what real Australian signs look like, NOT as training data unless properly licensed.

## Report
Write to `/tmp/news_fuel_images_results.md`:
- Article URLs with fuel sign photos
- Image descriptions (brand, fuels, prices, quality)
- Visual validation results
- Licensing notes

## Failure Condition
If no fuel sign images found on news sites or none visually validated → TASK FAILED.
