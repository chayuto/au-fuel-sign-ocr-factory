# Agent Prompt: Find Australian Fuel Sign Images & Price APIs

## Objective
Find freely available Australian fuel station price sign images from the web, and identify government fuel price APIs for ground truth data.

## Part 1: Image Sources

### Search Queries
- "Australian petrol station price board photo"
- "fuel sign Australia"
- "servo price board Australia"
- "fuel price board LED sign"
- creative commons fuel station images

### Steps
1. **Web Search** for image sources: news articles, Flickr CC, Wikimedia Commons, stock photo sites (free tier).
2. For promising sources, download a sample image to `/tmp/au_fuel_sample_*.jpg` and use Read to visually verify it shows an Australian fuel price sign.
3. Note licensing for each source (CC-BY, CC0, editorial use only, etc.).

## Part 2: Fuel Price APIs (Ground Truth)

### Search Queries
- "FuelCheck NSW API"
- "FuelWatch WA API"
- "Queensland fuel price API"
- "Australian fuel price data API"
- "ACCC fuel price monitoring"

### Steps
1. **Web Search** for each state's fuel price API.
2. Use WebFetch to check API documentation — endpoints, data format, rate limits, registration requirements.
3. Document each API's capabilities:
   - Real-time prices? Historical?
   - By station? By fuel type?
   - Free / registration required?

## Part 3: Visual Validation (HARD REQUIREMENT)
You MUST visually validate at least one real Australian fuel sign image. Download it and use Read to view it. Confirm it shows an actual Australian fuel price sign with legible fuel types and prices.

## Report
Write to `/tmp/au_fuel_sources_results.md`:
- Image sources with licensing info
- API endpoints and capabilities
- Visual validation evidence
- Recommendations for bootstrapping a dataset

## Failure Condition
If no Australian fuel sign images can be visually validated → TASK FAILED.
