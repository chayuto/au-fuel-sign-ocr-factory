#!/usr/bin/env python3
"""Train the Fuel Type Classifier (8-class SimpleCNN).

Prerequisites:
    python scripts/extract_label_crops.py   # extract training crops first

Usage:
    PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python scripts/train_fuel_type_classifier.py \
        --data data/classifier/fuel_type \
        --output runs/classifier/fuel_type_v1 \
        --epochs 60 --batch-size 64 --lr 0.001
"""

import argparse
import json
import os
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from au_fuel_sign_ocr_factory.classifier.fuel_type_model import (
    FUEL_TYPES,
    FuelTypeCNN,
    count_parameters,
)


class FuelTypeCropDataset(Dataset):
    """Load label crops from directory structure: {split}/{fuel_type}/*.jpg"""

    def __init__(self, root_dir: Path, img_size: tuple[int, int] = (48, 128), augment: bool = False):
        self.img_size = img_size  # H, W
        self.augment = augment
        self.samples = []  # (path, class_idx)

        self.type_to_idx = {ft: i for i, ft in enumerate(FUEL_TYPES)}

        for fuel_type in FUEL_TYPES:
            type_dir = root_dir / fuel_type
            if not type_dir.exists():
                continue
            for f in sorted(type_dir.iterdir()):
                if f.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    self.samples.append((f, self.type_to_idx[fuel_type]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(str(path))
        if img is None:
            img = np.zeros((self.img_size[0], self.img_size[1], 3), dtype=np.uint8)

        img = cv2.resize(img, (self.img_size[1], self.img_size[0]))

        if self.augment:
            # Simple augmentations
            if np.random.rand() < 0.3:
                # Brightness jitter
                factor = np.random.uniform(0.7, 1.3)
                img = np.clip(img * factor, 0, 255).astype(np.uint8)
            if np.random.rand() < 0.2:
                # Gaussian noise
                noise = np.random.normal(0, 10, img.shape).astype(np.int16)
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # HWC BGR → CHW RGB, normalize to [0, 1]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(img).float().permute(2, 0, 1) / 255.0
        return tensor, label


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = criterion(logits, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)
        _, pred = logits.max(dim=1)
        correct += (pred == y).sum().item()
        total += x.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    per_class_correct = [0] * len(FUEL_TYPES)
    per_class_total = [0] * len(FUEL_TYPES)

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = criterion(logits, y)

        total_loss += loss.item() * x.size(0)
        _, pred = logits.max(dim=1)
        correct += (pred == y).sum().item()
        total += x.size(0)

        for i in range(len(FUEL_TYPES)):
            mask = y == i
            per_class_total[i] += mask.sum().item()
            per_class_correct[i] += ((pred == i) & mask).sum().item()

    per_class_acc = {
        FUEL_TYPES[i]: per_class_correct[i] / per_class_total[i]
        if per_class_total[i] > 0 else 0.0
        for i in range(len(FUEL_TYPES))
    }
    return total_loss / total, correct / total, per_class_acc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Data root (with train/val subdirs)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", default=None, help="Device (auto-detect if omitted)")
    args = parser.parse_args()

    data_root = Path(args.data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Device
    if args.device:
        device = torch.device(args.device)
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Device: {device}")

    # Data
    train_ds = FuelTypeCropDataset(data_root / "train", augment=True)
    val_ds = FuelTypeCropDataset(data_root / "val", augment=False)
    print(f"Train: {len(train_ds)} samples, Val: {len(val_ds)} samples")

    if len(train_ds) == 0:
        print("ERROR: No training data. Run scripts/extract_label_crops.py first.")
        return

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    # Model
    model = FuelTypeCNN().to(device)
    print(f"Parameters: {count_parameters(model):,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # Training loop
    best_val_acc = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, per_class = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
        })

        print(
            f"Epoch {epoch:3d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.3f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.3f} | "
            f"{elapsed:.1f}s"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "model": model,
                "model_state_dict": model.state_dict(),
                "epoch": epoch,
                "val_acc": val_acc,
                "fuel_types": FUEL_TYPES,
            }, output_dir / "best.pt")
            print(f"  → Saved best model (val_acc={val_acc:.3f})")

    # Save final
    torch.save({
        "model": model,
        "model_state_dict": model.state_dict(),
        "epoch": args.epochs,
        "val_acc": val_acc,
        "fuel_types": FUEL_TYPES,
    }, output_dir / "last.pt")

    # Save history
    with open(output_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    # Final per-class report
    print(f"\nBest val accuracy: {best_val_acc:.3f}")
    print(f"\nPer-class accuracy (final epoch):")
    for ft, acc in per_class.items():
        print(f"  {ft:<10} {acc:.3f}")


if __name__ == "__main__":
    main()
