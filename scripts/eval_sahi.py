"""EXP-031: SAHI vs standard inference mAP eval on canonical_test_v2 (50 imgs).

Compares: standard YOLO inference vs SAHI sliced inference (320x320 and 480x480 slices)
using the new best Finder model (exp029_treatment_s42).
"""

import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image
from torchmetrics.detection import MeanAveragePrecision

ROOT = Path(__file__).resolve().parent.parent
TEST_IMAGES = ROOT / "data/finder_canonical_test_v2/images/test"
TEST_LABELS = ROOT / "data/finder_canonical_test_v2/labels/test"
DEFAULT_MODEL = ROOT / "runs/detect/runs/finder/exp029_treatment_s42/weights/best.pt"


def load_gt(label_path: Path, img_w: int, img_h: int):
    """Load YOLO format labels and convert to absolute xyxy."""
    boxes = []
    if not label_path.exists():
        return torch.zeros((0, 4)), torch.zeros((0,), dtype=torch.long)
    for line in label_path.read_text().strip().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cls = int(parts[0])
        cx, cy, w, h = (float(x) for x in parts[1:5])
        x1 = (cx - w / 2) * img_w
        y1 = (cy - h / 2) * img_h
        x2 = (cx + w / 2) * img_w
        y2 = (cy + h / 2) * img_h
        boxes.append([x1, y1, x2, y2, cls])
    if not boxes:
        return torch.zeros((0, 4)), torch.zeros((0,), dtype=torch.long)
    arr = torch.tensor(boxes)
    return arr[:, :4], arr[:, 4].long()


def run_standard(model_path: Path, conf: float = 0.001):
    """Standard YOLO inference at 640x640."""
    from ultralytics import YOLO

    model = YOLO(str(model_path))
    metric = MeanAveragePrecision(box_format="xyxy", iou_type="bbox")

    images = sorted([p for p in TEST_IMAGES.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    t0 = time.time()
    for img_path in images:
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        results = model.predict(str(img_path), conf=conf, imgsz=640, device="mps", verbose=False)
        r = results[0]
        if r.boxes is not None and len(r.boxes) > 0:
            preds = {
                "boxes": r.boxes.xyxy.cpu(),
                "scores": r.boxes.conf.cpu(),
                "labels": r.boxes.cls.long().cpu(),
            }
        else:
            preds = {"boxes": torch.zeros((0, 4)), "scores": torch.zeros((0,)), "labels": torch.zeros((0,), dtype=torch.long)}
        gt_boxes, gt_labels = load_gt(TEST_LABELS / (img_path.stem + ".txt"), w, h)
        targets = {"boxes": gt_boxes, "labels": gt_labels}
        metric.update([preds], [targets])
    dt = time.time() - t0
    res = metric.compute()
    return {
        "mAP50": float(res["map_50"]),
        "mAP50-95": float(res["map"]),
        "mAR_100": float(res["mar_100"]),
        "n_images": len(images),
        "wall_seconds": dt,
        "ms_per_image": dt * 1000 / len(images),
    }


def run_sahi(model_path: Path, slice_size: int, overlap: float = 0.2, conf: float = 0.001):
    """SAHI sliced inference with given slice size."""
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction

    model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=str(model_path),
        confidence_threshold=conf,
        device="mps",
    )
    metric = MeanAveragePrecision(box_format="xyxy", iou_type="bbox")

    images = sorted([p for p in TEST_IMAGES.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    t0 = time.time()
    for img_path in images:
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        result = get_sliced_prediction(
            str(img_path),
            model,
            slice_height=slice_size,
            slice_width=slice_size,
            overlap_height_ratio=overlap,
            overlap_width_ratio=overlap,
            verbose=0,
        )
        boxes, scores, labels = [], [], []
        for op in result.object_prediction_list:
            bb = op.bbox  # has minx, miny, maxx, maxy
            boxes.append([bb.minx, bb.miny, bb.maxx, bb.maxy])
            scores.append(op.score.value)
            labels.append(op.category.id)
        if boxes:
            preds = {
                "boxes": torch.tensor(boxes, dtype=torch.float),
                "scores": torch.tensor(scores, dtype=torch.float),
                "labels": torch.tensor(labels, dtype=torch.long),
            }
        else:
            preds = {"boxes": torch.zeros((0, 4)), "scores": torch.zeros((0,)), "labels": torch.zeros((0,), dtype=torch.long)}
        gt_boxes, gt_labels = load_gt(TEST_LABELS / (img_path.stem + ".txt"), w, h)
        targets = {"boxes": gt_boxes, "labels": gt_labels}
        metric.update([preds], [targets])
    dt = time.time() - t0
    res = metric.compute()
    return {
        "mAP50": float(res["map_50"]),
        "mAP50-95": float(res["map"]),
        "mAR_100": float(res["mar_100"]),
        "n_images": len(images),
        "wall_seconds": dt,
        "ms_per_image": dt * 1000 / len(images),
        "slice_size": slice_size,
        "overlap": overlap,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=str(DEFAULT_MODEL))
    p.add_argument("--mode", choices=["standard", "sahi320", "sahi480", "all"], default="all")
    p.add_argument("--out", default=str(ROOT / "logs/exp031_results.json"))
    args = p.parse_args()

    model_path = Path(args.model)
    assert model_path.exists(), f"Model not found: {model_path}"
    print(f"Model: {model_path}")
    print(f"Test set: {TEST_IMAGES} ({len(list(TEST_IMAGES.iterdir()))} images)")

    results = {}

    if args.mode in ("standard", "all"):
        print("\n=== Standard inference (640x640) ===")
        results["standard"] = run_standard(model_path)
        print(json.dumps(results["standard"], indent=2))

    if args.mode in ("sahi320", "all"):
        print("\n=== SAHI 320x320 slices ===")
        results["sahi_320"] = run_sahi(model_path, slice_size=320, overlap=0.2)
        print(json.dumps(results["sahi_320"], indent=2))

    if args.mode in ("sahi480", "all"):
        print("\n=== SAHI 480x480 slices ===")
        results["sahi_480"] = run_sahi(model_path, slice_size=480, overlap=0.2)
        print(json.dumps(results["sahi_480"], indent=2))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2))
    print(f"\nResults written to {args.out}")

    # Summary
    if len(results) > 1:
        print("\n=== Summary ===")
        print(f"{'method':<15} {'mAP50':>8} {'mAP50-95':>10} {'mAR_100':>10} {'ms/img':>10}")
        for k, v in results.items():
            print(f"{k:<15} {v['mAP50']:>8.4f} {v['mAP50-95']:>10.4f} {v['mAR_100']:>10.4f} {v['ms_per_image']:>10.1f}")


if __name__ == "__main__":
    main()
