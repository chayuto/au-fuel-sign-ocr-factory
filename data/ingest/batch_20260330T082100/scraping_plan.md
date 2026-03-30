# Wikimedia Commons Scraping Plan

## Environment Status
- **Issue**: No internet connectivity available in current environment
- **Batch Directory**: `/home/runner/work/au-fuel-sign-ocr-factory/au-fuel-sign-ocr-factory/data/ingest/batch_20260330T082100`
- **Target Brands**: Costco (CRITICAL), Metro Petroleum (CRITICAL), 7-Eleven, Liberty, OTR

## API Endpoints to Try (when internet is available)

### Priority Brand Searches
```bash
# Costco fuel stations
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=Costco+fuel+Australia&srnamespace=6&srlimit=20&format=json"

# Metro Petroleum
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=Metro+petroleum+Australia&srnamespace=6&srlimit=20&format=json"

# 7-Eleven with price signs
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=7-Eleven+petrol+Australia+price&srnamespace=6&srlimit=20&format=json"

# Liberty Oil
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=Liberty+Oil+petrol+Australia&srnamespace=6&srlimit=20&format=json"
```

### Category Searches
```bash
# General Australian petrol stations
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Petrol_stations_in_Australia&cmtype=file&cmlimit=50&format=json"

# State-specific searches
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Petrol_stations_in_Victoria,_Australia&cmtype=file&cmlimit=50&format=json"
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Petrol_stations_in_New_South_Wales&cmtype=file&cmlimit=50&format=json"
```

## Workflow Script (Ready to Execute)

```bash
#!/bin/bash
BATCH_DIR="/home/runner/work/au-fuel-sign-ocr-factory/au-fuel-sign-ocr-factory/data/ingest/batch_20260330T082100"
mkdir -p "$BATCH_DIR"

# Function to get image URL from filename
get_image_url() {
    local filename="$1"
    curl -s "https://commons.wikimedia.org/w/api.php?action=query&titles=File:$filename&prop=imageinfo&iiprop=url&iiurlwidth=1024&format=json" | \
    jq -r '.query.pages[].imageinfo[0].url // empty'
}

# Function to download and verify image
download_image() {
    local url="$1"
    local output_file="$2"
    
    curl -sL -o "$output_file" "$url"
    
    # Verify file exists and is > 1KB
    if [[ -f "$output_file" ]] && [[ $(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null) -gt 1024 ]]; then
        echo "Downloaded: $output_file ($(ls -lh "$output_file" | awk '{print $5}'))"
        return 0
    else
        rm -f "$output_file"
        echo "Failed or too small: $output_file"
        return 1
    fi
}

# Search and download process would go here
# This script is ready to run when internet connectivity is restored
```

## File Naming Convention
- `{source}_{brand}_{location}_{detail}.{ext}`
- Examples: `wiki_costco_auburn_nsw.jpg`, `wiki_metro_perth_wa.jpg`

## Quality Criteria
- Must contain fuel price sign board
- Price numbers must be visible
- Fuel type labels must be visible
- File size > 1KB

## Next Steps
1. Restore internet connectivity
2. Execute API searches
3. Filter for images with visible price signs
4. Download with proper naming
5. Commit to git

## Status
**BLOCKED**: No internet connectivity available for scraping