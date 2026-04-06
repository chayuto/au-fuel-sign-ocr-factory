#!/usr/bin/env python3
"""
Scrape Google Image Search thumbnails using Playwright.

Usage:
    npx playwright install chromium  # first time only
    python scripts/scrape_google_images.py --query "Costco fuel Australia price sign" --brand costco --max 30
    python scripts/scrape_google_images.py --query "Metro Petroleum price sign" --brand metro --max 30
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone


def run_playwright_scrape(query: str, max_images: int = 30) -> list[dict]:
    """Use Playwright via Node.js to scrape Bing Image Search results."""

    js_script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch({{ headless: true }});
    const context = await browser.newContext({{
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }});
    const page = await context.newPage();

    const query = {json.dumps(query)};
    const url = `https://www.bing.com/images/search?q=${{encodeURIComponent(query)}}&form=HDRSC2`;

    await page.goto(url, {{ waitUntil: 'networkidle', timeout: 30000 }});

    // Scroll down to load more images
    for (let i = 0; i < 5; i++) {{
        await page.evaluate(() => window.scrollBy(0, 1500));
        await page.waitForTimeout(1500);
    }}

    // Bing image results are in a.iusc elements with JSON in 'm' attribute
    const images = await page.evaluate(() => {{
        const results = [];
        document.querySelectorAll('a.iusc').forEach(a => {{
            try {{
                const m = JSON.parse(a.getAttribute('m') || '{{}}');
                if (m.murl) {{
                    results.push({{
                        src: m.murl,
                        thumb: m.turl || '',
                        alt: (m.t || '').substring(0, 200),
                    }});
                }}
            }} catch(e) {{}}
        }});
        return results;
    }});

    console.log(JSON.stringify(images));
    await browser.close();
}})();
"""

    result = subprocess.run(
        ["node", "-e", js_script],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "NODE_PATH": subprocess.run(
            ["npm", "root", "-g"], capture_output=True, text=True
        ).stdout.strip()},
    )

    if result.returncode != 0:
        print(f"Playwright error: {result.stderr}", file=sys.stderr)
        return []

    try:
        images = json.loads(result.stdout.strip())
        return images[:max_images]
    except json.JSONDecodeError:
        print(f"Failed to parse output: {result.stdout[:200]}", file=sys.stderr)
        return []


def download_image(url: str, filepath: Path) -> bool:
    """Download an image, return True if successful."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-o", str(filepath), "-m", "10", url],
            capture_output=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False

        # Verify it's actually an image and > 5KB
        if not filepath.exists():
            return False
        size = filepath.stat().st_size
        if size < 5120:
            filepath.unlink()
            return False

        # Check MIME type
        mime_result = subprocess.run(
            ["file", "-b", "--mime-type", str(filepath)],
            capture_output=True,
            text=True,
        )
        if not mime_result.stdout.strip().startswith("image/"):
            filepath.unlink()
            return False

        return True
    except Exception:
        if filepath.exists():
            filepath.unlink()
        return False


def dedup_check(name: str) -> bool:
    """Check if a similar file already exists in ingest or tmp."""
    keyword = name.split(".")[0].replace("_", " ").lower()
    # Simple keyword check
    for search_dir in ["data/ingest", "data/tmp"]:
        if Path(search_dir).exists():
            for f in Path(search_dir).rglob("*"):
                if any(k in f.name.lower() for k in keyword.split()[:2]):
                    return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Scrape Google Image Search thumbnails")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--brand", required=True, help="Brand name for filename")
    parser.add_argument("--max", type=int, default=30, help="Max images to download")
    parser.add_argument("--batch-dir", help="Override batch directory")
    args = parser.parse_args()

    # Create batch directory
    if args.batch_dir:
        batch_dir = Path(args.batch_dir)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        batch_dir = Path(f"data/ingest/batch_{ts}")
    batch_dir.mkdir(parents=True, exist_ok=True)

    print(f"Query: {args.query}")
    print(f"Brand: {args.brand}")
    print(f"Batch: {batch_dir}")
    print()

    # Scrape Google Images
    print("Launching Playwright to scrape Google Images...")
    images = run_playwright_scrape(args.query, args.max)
    print(f"Found {len(images)} image URLs")

    # Download and validate
    saved = 0
    rejected = 0
    for i, img in enumerate(images):
        url = img["src"]
        # Generate filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = "jpg"
        if ".png" in url.lower():
            ext = "png"
        name = f"gimg_{args.brand}_{url_hash}_{i:02d}.{ext}"
        filepath = batch_dir / name

        print(f"  [{i+1}/{len(images)}] Downloading {url[:80]}...")
        if download_image(url, filepath):
            saved += 1
            print(f"    -> Saved: {name} ({filepath.stat().st_size // 1024}KB)")
        else:
            rejected += 1
            print(f"    -> Rejected (too small or not an image)")

    # Write scrape report
    report = f"""# Scrape Report: v5 — Google Image Search (Playwright)

## Summary
- **Query:** {args.query}
- **Brand:** {args.brand}
- **Images found:** {len(images)}
- **Images saved:** {saved}
- **Images rejected:** {rejected}

## Quality Self-Check
These are Google Image thumbnails (~300px). They need visual screening
before labeling — many will be logos, infographics, or unrelated content.
Run Haiku screening on the full batch after ingest.

## Notes
- Source: Google Image Search via Playwright headless browser
- Images are thumbnails, not full-resolution originals
- Resolution is sufficient for YOLO training at 640px
"""
    (batch_dir / "scrape_report.md").write_text(report)

    print(f"\nDone! Saved {saved} images to {batch_dir}")
    print(f"Next: run Haiku screening to filter out non-sign images")


if __name__ == "__main__":
    main()
