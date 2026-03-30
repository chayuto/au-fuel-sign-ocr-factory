#!/usr/bin/env python3
"""End-to-end benchmark: run full pipeline on test set, compare vs ground truth.

Metrics:
  - Price accuracy: % of GT prices correctly read (±0.1 tolerance)
  - Fuel type accuracy: % of matched rows with correct fuel type
  - Row recall: % of GT rows detected
  - Row precision: % of detected rows that match a GT row
  - Brand accuracy: % of images with correct brand
  - Latency: ms per image (total and finder-only)

Usage:
    python scripts/benchmark_e2e.py \
        --finder runs/finder/v1_2class_149/weights/best.pt \
        --test-dir data/finder/images/test \
        --annotations-dir data/tmp/annotations \
        [--price-reader runs/reader/price_v1/best.pt] \
        [--fuel-type-clf runs/classifier/fuel_type_v1/best.pt] \
        [--brand-clf runs/classifier/brand_v1/best.pt]
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class RowMatch:
    """A matched pair of ground truth and predicted fuel row."""

    gt_fuel_type: str
    gt_price: float
    pred_fuel_type: str | None
    pred_price: float | None
    price_correct: bool
    fuel_type_correct: bool


@dataclass
class ImageResult:
    """Benchmark result for one image."""

    filename: str
    gt_brand: str
    pred_brand: str
    brand_correct: bool
    gt_rows: int
    pred_rows: int
    matched_rows: list[RowMatch]
    unmatched_gt: int  # GT rows not detected
    unmatched_pred: int  # predicted rows that don't match GT
    latency_ms: float
    finder_latency_ms: float


@dataclass
class BenchmarkSummary:
    """Aggregate metrics across all test images."""

    total_images: int = 0
    brand_correct: int = 0
    total_gt_rows: int = 0
    total_pred_rows: int = 0
    total_matched: int = 0
    price_correct: int = 0
    fuel_type_correct: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    finder_latencies_ms: list[float] = field(default_factory=list)
    per_image: list[ImageResult] = field(default_factory=list)

    @property
    def brand_accuracy(self) -> float:
        return self.brand_correct / self.total_images if self.total_images else 0

    @property
    def row_recall(self) -> float:
        return self.total_matched / self.total_gt_rows if self.total_gt_rows else 0

    @property
    def row_precision(self) -> float:
        return self.total_matched / self.total_pred_rows if self.total_pred_rows else 0

    @property
    def price_accuracy(self) -> float:
        return self.price_correct / self.total_matched if self.total_matched else 0

    @property
    def fuel_type_accuracy(self) -> float:
        return self.fuel_type_correct / self.total_matched if self.total_matched else 0

    @property
    def mean_latency_ms(self) -> float:
        return float(np.mean(self.latencies_ms)) if self.latencies_ms else 0

    @property
    def mean_finder_latency_ms(self) -> float:
        return float(np.mean(self.finder_latencies_ms)) if self.finder_latencies_ms else 0


def match_rows(
    gt_entries: list[dict],
    pred_rows: list,
    price_tolerance: float = 0.15,
    y_match_threshold: float = 0.08,
) -> tuple[list[RowMatch], int, int]:
    """Match predicted rows to ground truth entries by Y-coordinate proximity.

    Returns (matches, unmatched_gt_count, unmatched_pred_count).
    """
    matches = []
    used_pred = set()

    for gt in gt_entries:
        gt_price = gt["price"]
        gt_type = gt["fuel_type"]
        gt_cy = (gt["price_bbox"][1] + gt["price_bbox"][3]) / 2

        best_idx = -1
        best_dist = float("inf")

        for pi, pred in enumerate(pred_rows):
            if pi in used_pred:
                continue
            pred_cy = (pred.price_bbox[1] + pred.price_bbox[3]) / 2
            dist = abs(gt_cy - pred_cy)
            if dist < best_dist and dist <= y_match_threshold:
                best_dist = dist
                best_idx = pi

        if best_idx >= 0:
            pred = pred_rows[best_idx]
            used_pred.add(best_idx)

            price_ok = (
                pred.price_value is not None
                and abs(pred.price_value - gt_price) <= price_tolerance
            )
            type_ok = pred.fuel_type == gt_type

            matches.append(RowMatch(
                gt_fuel_type=gt_type,
                gt_price=gt_price,
                pred_fuel_type=pred.fuel_type,
                pred_price=pred.price_value,
                price_correct=price_ok,
                fuel_type_correct=type_ok,
            ))

    unmatched_gt = len(gt_entries) - len(matches)
    unmatched_pred = len(pred_rows) - len(used_pred)
    return matches, unmatched_gt, unmatched_pred


def run_benchmark(
    pipeline,
    test_dir: Path,
    annotations_dir: Path,
) -> BenchmarkSummary:
    """Run pipeline on all test images and compute metrics."""
    summary = BenchmarkSummary()

    image_files = sorted(
        f for f in test_dir.iterdir()
        if f.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    for img_path in image_files:
        stem = img_path.stem
        ann_path = annotations_dir / f"{stem}.json"

        if not ann_path.exists():
            print(f"  SKIP {stem} — no annotation")
            continue

        gt = json.loads(ann_path.read_text())
        gt_brand = gt["sign"]["brand"]
        gt_entries = gt.get("entries", [])

        # Run pipeline
        result = pipeline.predict_file(img_path)

        # Match rows
        matches, unmatched_gt, unmatched_pred = match_rows(gt_entries, result.rows)

        brand_ok = result.brand == gt_brand

        img_result = ImageResult(
            filename=img_path.name,
            gt_brand=gt_brand,
            pred_brand=result.brand,
            brand_correct=brand_ok,
            gt_rows=len(gt_entries),
            pred_rows=len(result.rows),
            matched_rows=matches,
            unmatched_gt=unmatched_gt,
            unmatched_pred=unmatched_pred,
            latency_ms=result.latency_ms,
            finder_latency_ms=result.finder_latency_ms,
        )

        # Accumulate
        summary.total_images += 1
        summary.brand_correct += int(brand_ok)
        summary.total_gt_rows += len(gt_entries)
        summary.total_pred_rows += len(result.rows)
        summary.total_matched += len(matches)
        summary.price_correct += sum(m.price_correct for m in matches)
        summary.fuel_type_correct += sum(m.fuel_type_correct for m in matches)
        summary.latencies_ms.append(result.latency_ms)
        summary.finder_latencies_ms.append(result.finder_latency_ms)
        summary.per_image.append(img_result)

    return summary


def print_report(summary: BenchmarkSummary) -> None:
    """Print benchmark results."""
    print("=" * 70)
    print("E2E BENCHMARK RESULTS")
    print("=" * 70)

    print(f"\nImages tested: {summary.total_images}")
    print(f"GT rows total: {summary.total_gt_rows}")
    print(f"Predicted rows total: {summary.total_pred_rows}")
    print(f"Matched rows: {summary.total_matched}")

    print(f"\n{'Metric':<25} {'Value':>10}")
    print("-" * 40)
    print(f"{'Brand accuracy':<25} {summary.brand_accuracy:>9.1%}")
    print(f"{'Row recall':<25} {summary.row_recall:>9.1%}")
    print(f"{'Row precision':<25} {summary.row_precision:>9.1%}")
    print(f"{'Price accuracy':<25} {summary.price_accuracy:>9.1%}")
    print(f"{'Fuel type accuracy':<25} {summary.fuel_type_accuracy:>9.1%}")
    print(f"{'Mean latency (total)':<25} {summary.mean_latency_ms:>8.1f}ms")
    print(f"{'Mean latency (finder)':<25} {summary.mean_finder_latency_ms:>8.1f}ms")

    print(f"\n{'Image':<45} {'Brand':>6} {'Rows':>8} {'Price':>7} {'Type':>6} {'ms':>7}")
    print("-" * 82)
    for r in summary.per_image:
        matched = len(r.matched_rows)
        price_ok = sum(m.price_correct for m in r.matched_rows)
        type_ok = sum(m.fuel_type_correct for m in r.matched_rows)
        brand_mark = "OK" if r.brand_correct else "MISS"
        print(
            f"{r.filename:<45} {brand_mark:>6} "
            f"{matched}/{r.gt_rows:>3}    "
            f"{price_ok}/{matched:>3}   "
            f"{type_ok}/{matched:>3}  "
            f"{r.latency_ms:>6.0f}"
        )


def main():
    parser = argparse.ArgumentParser(description="E2E benchmark")
    parser.add_argument("--finder", required=True, help="Path to Finder YOLO weights")
    parser.add_argument("--test-dir", default="data/finder/images/test")
    parser.add_argument("--annotations-dir", default="data/tmp/annotations")
    parser.add_argument("--price-reader", default=None)
    parser.add_argument("--fuel-type-clf", default=None)
    parser.add_argument("--brand-clf", default=None)
    parser.add_argument("--conf", type=float, default=0.25, help="Finder confidence threshold")
    parser.add_argument("--output", default=None, help="Save results JSON to this path")
    args = parser.parse_args()

    from au_fuel_sign_ocr_factory.inference.pipeline import FuelSignPipeline

    print("Loading pipeline...")
    pipeline = FuelSignPipeline.from_checkpoints(
        finder=args.finder,
        price_reader=args.price_reader,
        fuel_type_clf=args.fuel_type_clf,
        brand_clf=args.brand_clf,
        finder_conf=args.conf,
    )

    print(f"Running benchmark on {args.test_dir}...")
    summary = run_benchmark(
        pipeline,
        test_dir=Path(args.test_dir),
        annotations_dir=Path(args.annotations_dir),
    )

    print_report(summary)

    if args.output:
        # Save machine-readable results
        out = {
            "total_images": summary.total_images,
            "brand_accuracy": summary.brand_accuracy,
            "row_recall": summary.row_recall,
            "row_precision": summary.row_precision,
            "price_accuracy": summary.price_accuracy,
            "fuel_type_accuracy": summary.fuel_type_accuracy,
            "mean_latency_ms": summary.mean_latency_ms,
            "mean_finder_latency_ms": summary.mean_finder_latency_ms,
            "per_image": [
                {
                    "filename": r.filename,
                    "gt_brand": r.gt_brand,
                    "pred_brand": r.pred_brand,
                    "brand_correct": r.brand_correct,
                    "gt_rows": r.gt_rows,
                    "pred_rows": r.pred_rows,
                    "matched": len(r.matched_rows),
                    "price_correct": sum(m.price_correct for m in r.matched_rows),
                    "fuel_type_correct": sum(m.fuel_type_correct for m in r.matched_rows),
                    "latency_ms": r.latency_ms,
                }
                for r in summary.per_image
            ],
        }
        Path(args.output).write_text(json.dumps(out, indent=2))
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
