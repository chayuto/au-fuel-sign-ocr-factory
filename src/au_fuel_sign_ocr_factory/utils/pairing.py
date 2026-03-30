"""Spatial pairing: match fuel_label detections to fuel_price detections by proximity.

Labels and prices on the same row share a similar Y-center coordinate.
Labels are typically left of prices.
"""

from __future__ import annotations

from au_fuel_sign_ocr_factory.annotate.schema import BBox


def pair_labels_to_prices(
    label_bboxes: list[BBox],
    price_bboxes: list[BBox],
    y_threshold: float = 0.05,
) -> list[tuple[int, int]]:
    """Match label detections to price detections by Y-coordinate proximity.

    Args:
        label_bboxes: List of label bounding boxes.
        price_bboxes: List of price bounding boxes.
        y_threshold: Max normalized Y-center distance for a valid pair.

    Returns:
        List of (label_idx, price_idx) pairs. Unmatched detections are excluded.
    """
    if not label_bboxes or not price_bboxes:
        return []

    # Greedy matching: for each label, find the closest price by Y-center
    used_prices: set[int] = set()
    pairs: list[tuple[int, int, float]] = []

    for li, label in enumerate(label_bboxes):
        best_pi = -1
        best_dist = float("inf")
        for pi, price in enumerate(price_bboxes):
            if pi in used_prices:
                continue
            dy = abs(label.cy - price.cy)
            if dy < best_dist and dy <= y_threshold:
                # Label should generally be left of price
                if label.cx < price.cx:
                    best_dist = dy
                    best_pi = pi
        if best_pi >= 0:
            pairs.append((li, best_pi, best_dist))
            used_prices.add(best_pi)

    # Sort by Y position (top to bottom)
    pairs.sort(key=lambda p: label_bboxes[p[0]].cy)
    return [(li, pi) for li, pi, _ in pairs]
