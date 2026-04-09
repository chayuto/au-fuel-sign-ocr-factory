#!/usr/bin/env python3
"""Train Price Reader using fixed-position classification (no CTC).

Prices are XX.X or XXX.X → 4 digit heads predicting 0-9 or blank.
Avoids CTC alignment issues that plague CRNN with small datasets.

Usage:
    PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -u scripts/train_price_classifier.py \
        --data data/reader_experts/price \
        --output runs/reader/price_cls_v1 --epochs 100 --batch-size 32 --lr 0.001
"""

import argparse
import csv
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from au_fuel_sign_ocr_factory.reader.model import PriceClassifier, count_parameters

IMG_HEIGHT = 48
IMG_WIDTH = 160
BLANK_IDX = 10


def price_to_targets(price_text: str) -> list[int]:
    """Convert price string to 4 classification targets.

    "189.9" → [1, 8, 9, 9]  (hundreds=1, tens=8, ones=9, tenths=9)
    "89.9"  → [10, 8, 9, 9] (hundreds=blank, tens=8, ones=9, tenths=9)
    """
    # Normalize to XXX.X by left-padding
    parts = price_text.split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else '0'

    # Pad integer part to 3 digits
    integer_part = integer_part.zfill(3)

    targets = []
    for ch in integer_part[:3]:
        targets.append(int(ch))
    targets.append(int(decimal_part[0]))

    # Mark leading zeros as blank (for XX.X format like "89.9" → "089.9")
    if targets[0] == 0:
        targets[0] = BLANK_IDX

    return targets


def targets_to_price(targets: list[int]) -> str:
    """Convert 4 classification targets back to price string."""
    chars = []
    for i, t in enumerate(targets):
        if t == BLANK_IDX:
            continue
        chars.append(str(t))
        if i == 2:
            chars.append('.')
    return ''.join(chars)


class PriceClsDataset(Dataset):
    def __init__(self, root_dir: Path, augment: bool = False):
        self.root_dir = root_dir
        self.augment = augment
        self.samples = []

        labels_path = root_dir / "labels.csv"
        if labels_path.exists():
            with open(labels_path) as f:
                for row in csv.DictReader(f):
                    self.samples.append((row["filename"], row["label"]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        filename, label_text = self.samples[idx]
        img = cv2.imread(str(self.root_dir / filename), cv2.IMREAD_GRAYSCALE)
        if img is None:
            img = np.zeros((IMG_HEIGHT, IMG_WIDTH), dtype=np.uint8)

        img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))

        if self.augment:
            if np.random.rand() < 0.3:
                img = np.clip(img * np.random.uniform(0.7, 1.3), 0, 255).astype(np.uint8)
            if np.random.rand() < 0.2:
                noise = np.random.normal(0, 8, img.shape).astype(np.int16)
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            if np.random.rand() < 0.15:
                shift = np.random.randint(-3, 4)
                m = np.float32([[1, 0, shift], [0, 1, 0]])
                img = cv2.warpAffine(img, m, (IMG_WIDTH, IMG_HEIGHT),
                                     borderMode=cv2.BORDER_REPLICATE)

        tensor = torch.from_numpy(img).float() / 255.0
        tensor = tensor.unsqueeze(0)  # (1, H, W)

        targets = torch.tensor(price_to_targets(label_text), dtype=torch.long)
        return tensor, targets, label_text


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    total = 0

    for images, targets, _ in loader:
        images = images.to(device)
        targets = targets.to(device)  # (B, 4)

        logits_list = model(images)  # list of 4 x (B, 11)

        loss = sum(criterion(logits_list[i], targets[:, i]) for i in range(4))

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        total += images.size(0)

    return total_loss / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    total = 0
    field_correct = 0
    per_head_correct = [0] * 4
    per_head_total = [0] * 4

    for images, targets, texts in loader:
        images = images.to(device)
        targets = targets.to(device)

        logits_list = model(images)
        loss = sum(criterion(logits_list[i], targets[:, i]) for i in range(4))
        total_loss += loss.item() * images.size(0)
        total += images.size(0)

        # Per-head accuracy
        for i in range(4):
            preds = logits_list[i].argmax(dim=1)
            per_head_correct[i] += (preds == targets[:, i]).sum().item()
            per_head_total[i] += targets.size(0)

        # Field accuracy (all 4 heads correct)
        preds_all = torch.stack([l.argmax(dim=1) for l in logits_list], dim=1)  # (B, 4)
        field_correct += (preds_all == targets).all(dim=1).sum().item()

    head_accs = [per_head_correct[i] / per_head_total[i] if per_head_total[i] > 0 else 0
                 for i in range(4)]
    return {
        "loss": total_loss / total,
        "field_acc": field_correct / total,
        "head_accs": head_accs,
        "char_acc": sum(head_accs) / 4,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--synth", default=None, help="Path to synth data dir")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    data_root = Path(args.data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.device:
        device = torch.device(args.device)
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    print(f"Device: {device}")

    train_ds = PriceClsDataset(data_root / "train", augment=True)
    val_ds = PriceClsDataset(data_root / "val", augment=False)

    if args.synth:
        synth_ds = PriceClsDataset(Path(args.synth), augment=False)
        print(f"Synth: {len(synth_ds)} samples")
        train_ds = torch.utils.data.ConcatDataset([synth_ds, train_ds])

    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = PriceClassifier().to(device)
    print(f"PriceClassifier parameters: {count_parameters(model):,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_field_acc = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        history.append({
            "epoch": epoch, "train_loss": train_loss,
            "val_loss": val["loss"], "val_field_acc": val["field_acc"],
            "val_char_acc": val["char_acc"],
        })

        ha = val["head_accs"]
        print(
            f"Epoch {epoch:3d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={val['loss']:.4f} "
            f"field={val['field_acc']:.3f} "
            f"char={val['char_acc']:.3f} "
            f"heads=[{ha[0]:.2f},{ha[1]:.2f},{ha[2]:.2f},{ha[3]:.2f}] | "
            f"{elapsed:.1f}s"
        )

        if val["field_acc"] > best_field_acc:
            best_field_acc = val["field_acc"]
            torch.save({
                "model": model,
                "model_state_dict": model.state_dict(),
                "epoch": epoch,
                "val_field_acc": val["field_acc"],
                "val_char_acc": val["char_acc"],
            }, output_dir / "best.pt")
            print(f"  -> Saved best (field_acc={val['field_acc']:.3f})")

    torch.save({
        "model": model, "model_state_dict": model.state_dict(),
        "epoch": args.epochs,
    }, output_dir / "last.pt")

    with open(output_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nBest val field accuracy: {best_field_acc:.3f}")


if __name__ == "__main__":
    main()
