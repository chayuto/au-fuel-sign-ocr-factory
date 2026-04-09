#!/usr/bin/env python3
"""Generate synthetic price crop images for Reader pretraining.

Two rendering modes:
  1. LED-style: seven-segment digits (red/green/amber) on dark backgrounds
  2. Font-style: cv2.putText with varied fonts (fallback diversity)

Usage:
    .venv/bin/python scripts/generate_synth_prices.py --count 50000 --output data/reader_experts/price/synth
"""

import argparse
import csv
import random
from pathlib import Path

import cv2
import numpy as np


IMG_HEIGHT = 48
IMG_WIDTH = 160

# Seven-segment display: which segments are ON for each digit
# Segments indexed:  0=top, 1=top-right, 2=bot-right, 3=bottom, 4=bot-left, 5=top-left, 6=middle
SEGMENTS = {
    '0': [1, 1, 1, 1, 1, 1, 0],
    '1': [0, 1, 1, 0, 0, 0, 0],
    '2': [1, 1, 0, 1, 1, 0, 1],
    '3': [1, 1, 1, 1, 0, 0, 1],
    '4': [0, 1, 1, 0, 0, 1, 1],
    '5': [1, 0, 1, 1, 0, 1, 1],
    '6': [1, 0, 1, 1, 1, 1, 1],
    '7': [1, 1, 1, 0, 0, 0, 0],
    '8': [1, 1, 1, 1, 1, 1, 1],
    '9': [1, 1, 1, 1, 0, 1, 1],
}


def draw_segment(img, x, y, w, h, seg_idx, color, thickness):
    """Draw a single seven-segment line on the image."""
    # Segment positions relative to digit bounding box (x, y, w, h)
    hw = w // 2  # half width
    hh = h // 2  # half height
    t = thickness

    segments = [
        # 0: top horizontal
        ((x + t, y), (x + w - t, y)),
        # 1: top-right vertical
        ((x + w, y + t), (x + w, y + hh - t)),
        # 2: bot-right vertical
        ((x + w, y + hh + t), (x + w, y + h - t)),
        # 3: bottom horizontal
        ((x + t, y + h), (x + w - t, y + h)),
        # 4: bot-left vertical
        ((x, y + hh + t), (x, y + h - t)),
        # 5: top-left vertical
        ((x, y + t), (x, y + hh - t)),
        # 6: middle horizontal
        ((x + t, y + hh), (x + w - t, y + hh)),
    ]

    pt1, pt2 = segments[seg_idx]
    cv2.line(img, pt1, pt2, color, thickness, cv2.LINE_AA)


def draw_digit(img, digit_char, x, y, w, h, color, thickness):
    """Draw a seven-segment digit."""
    if digit_char not in SEGMENTS:
        return
    segs = SEGMENTS[digit_char]
    for i, on in enumerate(segs):
        if on:
            draw_segment(img, x, y, w, h, i, color, thickness)


def draw_decimal_point(img, x, y, h, color, radius):
    """Draw a decimal point dot."""
    cv2.circle(img, (x, y + h), radius, color, -1, cv2.LINE_AA)


def render_led_price(price_text: str) -> np.ndarray:
    """Render price text as LED seven-segment display."""
    img = np.zeros((IMG_HEIGHT, IMG_WIDTH), dtype=np.uint8)

    # Dark background with slight variation
    bg = random.randint(0, 35)
    img[:] = bg

    # Optional background texture/noise
    if random.random() < 0.4:
        noise = np.random.normal(0, random.uniform(2, 8), img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # LED color (grayscale intensity for bright digits)
    base_brightness = random.randint(160, 255)

    # Digit sizing
    chars = list(price_text)
    n_digits = sum(1 for c in chars if c != '.')

    # Calculate digit dimensions to fit
    digit_h = int(IMG_HEIGHT * random.uniform(0.55, 0.80))
    digit_w = int(digit_h * random.uniform(0.45, 0.65))
    dot_w = max(3, digit_w // 3)
    spacing = max(1, int(digit_w * random.uniform(0.1, 0.3)))
    seg_thickness = max(1, int(digit_w * random.uniform(0.12, 0.22)))

    total_w = n_digits * (digit_w + spacing) + dot_w
    start_x = max(2, (IMG_WIDTH - total_w) // 2 + random.randint(-8, 8))
    start_y = max(1, (IMG_HEIGHT - digit_h) // 2 + random.randint(-3, 3))

    x = start_x
    for ch in chars:
        # Per-digit brightness variation (simulates LED inconsistency)
        brightness = max(100, min(255, base_brightness + random.randint(-20, 20)))

        if ch == '.':
            r = max(1, seg_thickness // 2 + 1)
            draw_decimal_point(img, x + dot_w // 2, start_y, digit_h, brightness, r)
            x += dot_w + spacing // 2
        else:
            draw_digit(img, ch, x, start_y, digit_w, digit_h, brightness, seg_thickness)
            x += digit_w + spacing

    # Optional dim "ghost" segments (off segments faintly visible)
    if random.random() < 0.3:
        ghost_brightness = random.randint(15, 40)
        x = start_x
        for ch in chars:
            if ch == '.':
                x += dot_w + spacing // 2
            else:
                segs = SEGMENTS.get(ch, [0]*7)
                for i, on in enumerate(segs):
                    if not on:
                        draw_segment(img, x, start_y, digit_w, digit_h, i, ghost_brightness, max(1, seg_thickness - 1))
                x += digit_w + spacing

    # Post-processing
    # Slight blur (simulates camera defocus)
    if random.random() < 0.5:
        ksize = random.choice([3, 3, 5])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0)

    # Noise
    if random.random() < 0.6:
        noise = np.random.normal(0, random.uniform(3, 15), img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Brightness/contrast jitter
    if random.random() < 0.3:
        alpha = random.uniform(0.8, 1.2)
        beta = random.randint(-15, 15)
        img = np.clip(img * alpha + beta, 0, 255).astype(np.uint8)

    # Slight rotation
    if random.random() < 0.25:
        angle = random.uniform(-4, 4)
        m = cv2.getRotationMatrix2D((IMG_WIDTH // 2, IMG_HEIGHT // 2), angle, 1.0)
        img = cv2.warpAffine(img, m, (IMG_WIDTH, IMG_HEIGHT), borderMode=cv2.BORDER_REPLICATE)

    return img


def render_font_price(price_text: str) -> np.ndarray:
    """Render price with cv2 fonts (diverse non-LED styles)."""
    img = np.zeros((IMG_HEIGHT, IMG_WIDTH), dtype=np.uint8)

    # Varied backgrounds
    style = random.choice(["dark", "medium", "light"])
    if style == "dark":
        img[:] = random.randint(0, 50)
        text_color = random.randint(170, 255)
    elif style == "medium":
        img[:] = random.randint(70, 150)
        text_color = random.choice([random.randint(0, 50), random.randint(200, 255)])
    else:
        img[:] = random.randint(190, 255)
        text_color = random.randint(0, 70)

    font = random.choice([
        cv2.FONT_HERSHEY_SIMPLEX,
        cv2.FONT_HERSHEY_DUPLEX,
        cv2.FONT_HERSHEY_TRIPLEX,
    ])

    target_h = IMG_HEIGHT * random.uniform(0.5, 0.8)
    scale = 1.0
    for s in [x * 0.1 for x in range(5, 30)]:
        (tw, th), _ = cv2.getTextSize(price_text, font, s, 2)
        if th >= target_h:
            scale = s
            break

    (tw, th), baseline = cv2.getTextSize(price_text, font, scale, 2)
    x = max(0, (IMG_WIDTH - tw) // 2 + random.randint(-10, 10))
    y = max(th, (IMG_HEIGHT + th) // 2 + random.randint(-4, 4))
    thickness = random.choice([1, 2, 2, 3])

    cv2.putText(img, price_text, (x, y), font, scale, text_color, thickness)

    if random.random() < 0.4:
        ksize = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0)
    if random.random() < 0.5:
        noise = np.random.normal(0, random.uniform(5, 15), img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img


def random_price() -> str:
    """Generate a realistic AU fuel price string."""
    r = random.random()
    if r < 0.15:
        price = random.uniform(50.0, 110.0)   # LPG
    elif r < 0.30:
        price = random.uniform(100.0, 140.0)  # Low
    elif r < 0.75:
        price = random.uniform(140.0, 220.0)  # Standard
    else:
        price = random.uniform(220.0, 310.0)  # High/Diesel
    return f"{price:.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50000)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--led-pct", type=float, default=0.75,
                        help="Fraction of LED-style (vs font-style)")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = []
    n_led = 0
    for i in range(args.count):
        price_text = random_price()
        if random.random() < args.led_pct:
            img = render_led_price(price_text)
            n_led += 1
        else:
            img = render_font_price(price_text)

        fname = f"synth_{i:06d}.jpg"
        cv2.imwrite(str(out_dir / fname), img)
        samples.append((fname, price_text))

    with open(out_dir / "labels.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label"])
        for fname, label in samples:
            writer.writerow([fname, label])

    print(f"Generated {len(samples)} synthetic price images ({n_led} LED, {len(samples)-n_led} font)")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
