#!/usr/bin/env python3
"""
Scrape Bing Image Search thumbnails using Playwright.
Logs every image (saved + rejected) to pipeline_events.jsonl for full traceability.

Usage:
    npx playwright install chromium  # first time only
    python scripts/scrape_google_images.py --query "Costco fuel Australia price sign" --brand costco --max 30
    python scripts/scrape_google_images.py --query "Metro Petroleum price sign" --brand metro --max 30
"""

import argparse
import hashlib
import os
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone


def get_prompt_version():
    """Read prompt version from config."""
    path = "configs/prompt_version.json"
    if os.path.exists(path):
        return json.load(open(path)).get("version", "unknown")
    return "unknown"


def log_pipeline_event(image, action, agent, details=None):
    """Log a scrape event to pipeline_events.jsonl."""
    try:
        subprocess.run(
            [
                sys.executable, "scripts/pipeline_logger.py", "log",
                "--image", image,
                "--stage", "ingest",
                "--agent", agent,
                "--action", action,
                "--details", json.dumps(details or {}),
            ],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass  # Don't fail scraping if logging fails


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
                        source_page: m.purl || '',
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


def main():
    parser = argparse.ArgumentParser(description="Scrape Bing Image Search thumbnails")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--brand", required=True, help="Brand name for filename")
    parser.add_argument("--max", type=int, default=30, help="Max images to download")
    parser.add_argument("--batch-dir", help="Override batch directory")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    agent_id = f"scrape_bing_{args.brand}_{ts}"
    prompt_version = get_prompt_version()

    # Create batch directory
    if args.batch_dir:
        batch_dir = Path(args.batch_dir)
    else:
        batch_dir = Path(f"data/ingest/batch_{ts}")
    batch_dir.mkdir(parents=True, exist_ok=True)

    print(f"Query: {args.query}")
    print(f"Brand: {args.brand}")
    print(f"Batch: {batch_dir}")
    print(f"Agent: {agent_id}")
    print()

    # Scrape Bing Images
    print("Launching Playwright to scrape Bing Images...")
    images = run_playwright_scrape(args.query, args.max)
    print(f"Found {len(images)} image URLs")

    # Per-image tracking
    saved_images = []
    rejected_images = []

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
            size_kb = filepath.stat().st_size // 1024
            saved_images.append({
                "filename": name,
                "source_url": url,
                "source_page": img.get("source_page", ""),
                "alt_text": img.get("alt", ""),
                "size_kb": size_kb,
            })
            print(f"    -> Saved: {name} ({size_kb}KB)")

            # Log to pipeline
            log_pipeline_event(name, "scraped", agent_id, {
                "source_url": url[:200],
                "source_page": img.get("source_page", "")[:200],
                "query": args.query,
                "brand_target": args.brand,
                "size_kb": size_kb,
                "batch_dir": str(batch_dir),
            })
        else:
            rejected_images.append({
                "source_url": url,
                "reason": "download failed or too small or not image",
            })
            print(f"    -> Rejected (too small or not an image)")

            # Log rejection
            log_pipeline_event(name, "scrape_rejected", agent_id, {
                "source_url": url[:200],
                "reason": "download failed, too small, or not image",
                "query": args.query,
                "brand_target": args.brand,
            })

    # Write structured scrape manifest (machine-readable)
    scrape_manifest = {
        "agent": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": args.query,
        "brand_target": args.brand,
        "search_engine": "bing",
        "method": "playwright_headless",
        "prompt_version": prompt_version,
        "batch_dir": str(batch_dir),
        "results": {
            "urls_found": len(images),
            "saved": len(saved_images),
            "rejected": len(rejected_images),
            "yield_pct": round(100 * len(saved_images) / max(len(images), 1), 1),
        },
        "saved_images": saved_images,
        "rejected_images": rejected_images[:20],  # cap to avoid huge files
    }
    (batch_dir / "scrape_manifest.json").write_text(
        json.dumps(scrape_manifest, indent=2)
    )

    # Write human-readable report (backwards compatible)
    report = f"""# Scrape Report: {args.query}

## Provenance
- **Agent:** {agent_id}
- **Timestamp:** {scrape_manifest['timestamp']}
- **Search engine:** Bing (Playwright headless)
- **Query:** {args.query}
- **Brand target:** {args.brand}
- **Prompt version:** {prompt_version}
- **Batch dir:** {batch_dir}

## Results
- **URLs found:** {len(images)}
- **Images saved:** {len(saved_images)}
- **Images rejected:** {len(rejected_images)}
- **Yield:** {scrape_manifest['results']['yield_pct']}%

## Saved Images
| Filename | Source URL | Size |
|----------|-----------|------|
"""
    for img in saved_images:
        report += f"| {img['filename']} | {img['source_url'][:80]}... | {img['size_kb']}KB |\n"

    report += f"""
## Rejected ({len(rejected_images)} total)
"""
    for img in rejected_images[:10]:
        report += f"- {img['source_url'][:80]}... — {img['reason']}\n"

    (batch_dir / "scrape_report.md").write_text(report)

    print(f"\nDone! Saved {len(saved_images)} images to {batch_dir}")
    print(f"Manifest: {batch_dir}/scrape_manifest.json")
    print(f"Report: {batch_dir}/scrape_report.md")
    print(f"Events logged to: data/tmp/pipeline_events.jsonl")


if __name__ == "__main__":
    main()
