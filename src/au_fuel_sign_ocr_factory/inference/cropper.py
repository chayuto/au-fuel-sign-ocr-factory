"""Crop extraction from Finder detections.

Given YOLO Finder outputs (sign_board + fuel_price bounding boxes) and the
original image, produces:
  - price crops (one per fuel_price detection)
  - label crops (region left of each fuel_price, within sign_board)
  - sign_board crop (for brand classification)

All bounding boxes are in normalized [0,1] coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FuelRowCrops:
    """Crops for one fuel row — price region and label region."""

    price_crop: np.ndarray  # H x W x C
    label_crop: np.ndarray  # H x W x C
    price_bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 normalized
    label_bbox: tuple[float, float, float, float]  # derived: sign.x1, price.y1, price.x1, price.y2
    y_center: float  # for sorting top→bottom


@dataclass
class FinderCrops:
    """All crops extracted from one image."""

    sign_board_crop: np.ndarray | None  # for brand classifier
    sign_board_bbox: tuple[float, float, float, float] | None
    rows: list[FuelRowCrops]  # sorted top→bottom


def extract_crops(
    image: np.ndarray,
    sign_board_bbox: tuple[float, float, float, float] | None,
    fuel_price_bboxes: list[tuple[float, float, float, float]],
    label_pad_left: float = 0.0,
    label_pad_y: float = 0.02,
    min_crop_px: int = 4,
) -> FinderCrops:
    """Extract downstream crops from Finder detections.

    Args:
        image: Original image as HxWxC numpy array (uint8).
        sign_board_bbox: Normalized [x1, y1, x2, y2] of the sign board, or None.
        fuel_price_bboxes: List of normalized [x1, y1, x2, y2] for each fuel_price.
        label_pad_left: Extra padding on the left side of label crop (normalized).
        label_pad_y: Vertical padding for label crop (normalized).
        min_crop_px: Minimum crop size in pixels (skip if smaller).

    Returns:
        FinderCrops with sign_board crop and per-row price + label crops.
    """
    h, w = image.shape[:2]

    def crop_bbox(bbox: tuple[float, float, float, float]) -> np.ndarray | None:
        x1 = max(0, int(bbox[0] * w))
        y1 = max(0, int(bbox[1] * h))
        x2 = min(w, int(bbox[2] * w))
        y2 = min(h, int(bbox[3] * h))
        if x2 - x1 < min_crop_px or y2 - y1 < min_crop_px:
            return None
        return image[y1:y2, x1:x2].copy()

    # Sign board crop
    sign_crop = None
    if sign_board_bbox is not None:
        sign_crop = crop_bbox(sign_board_bbox)

    # Determine the left edge for label crops
    sign_x1 = sign_board_bbox[0] if sign_board_bbox is not None else 0.0

    # Sort fuel_price bboxes by Y center (top → bottom)
    sorted_prices = sorted(
        fuel_price_bboxes,
        key=lambda b: (b[1] + b[3]) / 2,
    )

    rows = []
    for price_bbox in sorted_prices:
        px1, py1, px2, py2 = price_bbox
        y_center = (py1 + py2) / 2

        # Price crop
        price_crop = crop_bbox(price_bbox)
        if price_crop is None:
            continue

        # Label crop: from sign_board left edge to price left edge, same Y band
        label_bbox = (
            max(0.0, sign_x1 - label_pad_left),
            max(0.0, py1 - label_pad_y),
            px1,
            min(1.0, py2 + label_pad_y),
        )
        # Ensure label region has positive width
        if label_bbox[2] <= label_bbox[0]:
            label_crop = None
            # Fallback: can't derive label region
        else:
            label_crop = crop_bbox(label_bbox)

        if label_crop is None:
            # Create a tiny placeholder so downstream doesn't crash
            label_crop = np.zeros((min_crop_px, min_crop_px, 3), dtype=np.uint8)

        rows.append(FuelRowCrops(
            price_crop=price_crop,
            label_crop=label_crop,
            price_bbox=price_bbox,
            label_bbox=label_bbox,
            y_center=y_center,
        ))

    return FinderCrops(
        sign_board_crop=sign_crop,
        sign_board_bbox=sign_board_bbox,
        rows=rows,
    )
