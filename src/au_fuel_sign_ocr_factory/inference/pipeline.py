"""End-to-end fuel sign OCR pipeline.

Chains: YOLO Finder → crop extraction → Price Reader + Fuel Type Classifier + Brand Classifier.

Usage:
    pipeline = FuelSignPipeline.from_checkpoints(
        finder="runs/finder/v1_2class_149/weights/best.pt",
        price_reader="runs/reader/price_v1/best.pt",       # optional
        fuel_type_clf="runs/classifier/fuel_type_v1/best.pt",  # optional
        brand_clf="runs/classifier/brand_v1/best.pt",       # optional
    )
    results = pipeline.predict(image)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from au_fuel_sign_ocr_factory.inference.cropper import extract_crops
from au_fuel_sign_ocr_factory.inference.models import (
    BrandClassifierProtocol,
    FuelTypeClassifierProtocol,
    PriceReaderProtocol,
    load_brand_classifier,
    load_fuel_type_classifier,
    load_price_reader,
)


@dataclass
class FuelRow:
    """One detected fuel entry (type + price)."""

    fuel_type: str  # canonical: U91, E10, P95, P98, Diesel, LPG, AdBlue, E85
    fuel_type_confidence: float
    price_text: str  # raw OCR output, e.g. "189.9"
    price_value: float | None  # parsed numeric, or None if unparseable
    price_confidence: float
    price_bbox: tuple[float, float, float, float]  # normalized x1,y1,x2,y2
    label_bbox: tuple[float, float, float, float]  # derived


@dataclass
class PipelineResult:
    """Full structured output from one image."""

    brand: str
    brand_confidence: float
    sign_bbox: tuple[float, float, float, float] | None
    rows: list[FuelRow] = field(default_factory=list)
    latency_ms: float = 0.0
    finder_latency_ms: float = 0.0


# Price validation
PRICE_MIN = 50.0
PRICE_MAX = 400.0
PRICE_PATTERN_RE = None  # lazy import


def _parse_price(text: str) -> float | None:
    """Parse price text to float. Returns None if invalid."""
    import re

    global PRICE_PATTERN_RE
    if PRICE_PATTERN_RE is None:
        PRICE_PATTERN_RE = re.compile(r"^\d{1,3}\.\d$")

    text = text.strip()
    if not PRICE_PATTERN_RE.match(text):
        return None
    val = float(text)
    if PRICE_MIN <= val <= PRICE_MAX:
        return val
    return None


class FuelSignPipeline:
    """End-to-end inference pipeline."""

    def __init__(
        self,
        finder_model,
        price_reader: PriceReaderProtocol,
        fuel_type_clf: FuelTypeClassifierProtocol,
        brand_clf: BrandClassifierProtocol,
        finder_conf: float = 0.25,
    ):
        self.finder = finder_model
        self.price_reader = price_reader
        self.fuel_type_clf = fuel_type_clf
        self.brand_clf = brand_clf
        self.finder_conf = finder_conf

    @classmethod
    def from_checkpoints(
        cls,
        finder: str | Path,
        price_reader: str | Path | None = None,
        fuel_type_clf: str | Path | None = None,
        brand_clf: str | Path | None = None,
        finder_conf: float = 0.25,
    ) -> FuelSignPipeline:
        """Load pipeline from checkpoint paths. Missing checkpoints use stubs."""
        from ultralytics import YOLO

        finder_model = YOLO(str(finder))
        return cls(
            finder_model=finder_model,
            price_reader=load_price_reader(price_reader),
            fuel_type_clf=load_fuel_type_classifier(fuel_type_clf),
            brand_clf=load_brand_classifier(brand_clf),
            finder_conf=finder_conf,
        )

    def _run_finder(self, image: np.ndarray) -> tuple[
        tuple[float, float, float, float] | None,
        list[tuple[float, float, float, float]],
        float,
    ]:
        """Run YOLO Finder. Returns (sign_board_bbox, fuel_price_bboxes, latency_ms)."""
        t0 = time.perf_counter()
        results = self.finder.predict(image, conf=self.finder_conf, verbose=False)
        latency = (time.perf_counter() - t0) * 1000

        h, w = image.shape[:2]
        sign_bbox = None
        price_bboxes = []

        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i])
                # Normalized coordinates
                x1, y1, x2, y2 = boxes.xyxyn[i].tolist()
                bbox = (x1, y1, x2, y2)

                if cls_id == 0:  # sign_board
                    sign_bbox = bbox
                elif cls_id == 1:  # fuel_price (remapped from class 3)
                    price_bboxes.append(bbox)

        return sign_bbox, price_bboxes, latency

    def predict(self, image: np.ndarray) -> PipelineResult:
        """Run full pipeline on a single image.

        Args:
            image: BGR uint8 numpy array (as loaded by cv2.imread).

        Returns:
            PipelineResult with brand, rows, and timing.
        """
        t_start = time.perf_counter()

        # Step 1: Finder
        sign_bbox, price_bboxes, finder_ms = self._run_finder(image)

        # Step 2: Crop extraction
        crops = extract_crops(image, sign_bbox, price_bboxes)

        # Step 3: Brand classification
        brand = "unknown"
        brand_conf = 0.0
        if crops.sign_board_crop is not None:
            brand, brand_conf = self.brand_clf.predict(crops.sign_board_crop)

        # Step 4: Per-row reading
        rows = []
        for row_crop in crops.rows:
            # Price reading
            price_text, price_conf = self.price_reader.predict(row_crop.price_crop)
            price_value = _parse_price(price_text)

            # Fuel type classification
            fuel_type, ft_conf = self.fuel_type_clf.predict(row_crop.label_crop)

            rows.append(FuelRow(
                fuel_type=fuel_type,
                fuel_type_confidence=ft_conf,
                price_text=price_text,
                price_value=price_value,
                price_confidence=price_conf,
                price_bbox=row_crop.price_bbox,
                label_bbox=row_crop.label_bbox,
            ))

        total_ms = (time.perf_counter() - t_start) * 1000

        return PipelineResult(
            brand=brand,
            brand_confidence=brand_conf,
            sign_bbox=sign_bbox,
            rows=rows,
            latency_ms=total_ms,
            finder_latency_ms=finder_ms,
        )

    def predict_file(self, image_path: str | Path) -> PipelineResult:
        """Convenience: load image from file and run pipeline."""
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        return self.predict(image)
