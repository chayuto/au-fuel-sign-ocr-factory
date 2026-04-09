#!/usr/bin/env python3
"""Train the Price Reader (SimpleCRNN with CTC loss).

Prerequisites:
    python scripts/extract_price_crops.py   # extract training crops first

Usage:
    PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python -u scripts/train_reader.py \
        --expert price --data data/reader_experts/price \
        --output runs/reader/price_v1 --epochs 80 --batch-size 64 --lr 0.001
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
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

from au_fuel_sign_ocr_factory.reader.model import SimpleCRNN, SimpleCRNNTiny, count_parameters
from au_fuel_sign_ocr_factory.reader.vocab import Vocab

IMG_HEIGHT = 48
IMG_MAX_WIDTH = 320
IMG_FIXED_WIDTH = 160  # fixed width for consistent CTC alignment


class PriceReaderDataset(Dataset):
    """Load price crops with CTC labels.

    Directory structure:
        {split}/
            labels.csv       # filename,label
            *.jpg            # grayscale crops (height=48, variable width)
    """

    def __init__(self, root_dir: Path, vocab: Vocab, augment: bool = False):
        self.root_dir = root_dir
        self.vocab = vocab
        self.augment = augment
        self.samples = []  # (filename, label_text)

        labels_path = root_dir / "labels.csv"
        if labels_path.exists():
            with open(labels_path) as f:
                for row in csv.DictReader(f):
                    self.samples.append((row["filename"], row["label"]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        filename, label_text = self.samples[idx]
        img_path = self.root_dir / filename

        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            img = np.zeros((IMG_HEIGHT, 40), dtype=np.uint8)

        # Resize to fixed dimensions for consistent CTC alignment
        img = cv2.resize(img, (IMG_FIXED_WIDTH, IMG_HEIGHT))

        if self.augment:
            if np.random.rand() < 0.3:
                factor = np.random.uniform(0.7, 1.3)
                img = np.clip(img * factor, 0, 255).astype(np.uint8)
            if np.random.rand() < 0.2:
                noise = np.random.normal(0, 8, img.shape).astype(np.int16)
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            if np.random.rand() < 0.15:
                # Slight horizontal shift (up to 3px)
                shift = np.random.randint(-3, 4)
                m = np.float32([[1, 0, shift], [0, 1, 0]])
                img = cv2.warpAffine(img, m, (img.shape[1], img.shape[0]),
                                     borderMode=cv2.BORDER_REPLICATE)

        # Normalize to [0, 1], add channel dim
        tensor = torch.from_numpy(img).float() / 255.0  # (H, W)
        tensor = tensor.unsqueeze(0)  # (1, H, W)

        # Encode label
        target = torch.tensor(self.vocab.encode(label_text), dtype=torch.long)

        return tensor, target, label_text


def collate_fn(batch):
    """Stack fixed-width images, concatenate targets for CTC."""
    images, targets, texts = zip(*batch)

    images_batch = torch.stack(images)  # (B, 1, H, W) — all same W now
    target_concat = torch.cat(targets)  # flat concatenation for CTC
    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    # T = W // 4 after CNN pooling
    t_len = images_batch.shape[3] // 4
    input_lengths = torch.full((len(images),), t_len, dtype=torch.long)

    return images_batch, target_concat, input_lengths, target_lengths, texts


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    total_samples = 0

    for images, targets, input_lengths, target_lengths, _ in loader:
        images = images.to(device)
        targets = targets.to(device)
        input_lengths = input_lengths.to(device)
        target_lengths = target_lengths.to(device)

        logits = model(images)  # (T, B, C)
        log_probs = logits.log_softmax(dim=2)

        # Clamp input lengths to actual sequence length
        t_len = log_probs.size(0)
        input_lengths = input_lengths.clamp(max=t_len)

        loss = criterion(log_probs, targets, input_lengths, target_lengths)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        total_samples += images.size(0)

    return total_loss / total_samples


@torch.no_grad()
def evaluate(model, loader, criterion, vocab, device):
    model.eval()
    total_loss = 0
    total_samples = 0
    char_correct = 0
    char_total = 0
    field_correct = 0
    field_total = 0

    for images, targets, input_lengths, target_lengths, texts in loader:
        images = images.to(device)
        targets = targets.to(device)
        input_lengths = input_lengths.to(device)
        target_lengths = target_lengths.to(device)

        logits = model(images)  # (T, B, C)
        log_probs = logits.log_softmax(dim=2)

        t_len = log_probs.size(0)
        input_lengths_clamped = input_lengths.clamp(max=t_len)

        loss = criterion(log_probs, targets, input_lengths_clamped, target_lengths)
        total_loss += loss.item() * images.size(0)
        total_samples += images.size(0)

        # Greedy CTC decode
        _, indices = logits.max(dim=2)  # (T, B)
        for b in range(images.size(0)):
            pred_text = vocab.ctc_decode(indices[:, b].tolist())
            gt_text = texts[b]

            # Field accuracy (exact match)
            field_total += 1
            if pred_text == gt_text:
                field_correct += 1

            # Character accuracy
            for i, c in enumerate(gt_text):
                char_total += 1
                if i < len(pred_text) and pred_text[i] == c:
                    char_correct += 1
            # Penalize extra predicted chars
            if len(pred_text) > len(gt_text):
                char_total += len(pred_text) - len(gt_text)

    metrics = {
        "loss": total_loss / total_samples,
        "char_acc": char_correct / char_total if char_total > 0 else 0,
        "field_acc": field_correct / field_total if field_total > 0 else 0,
    }
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expert", default="price", help="Expert name from reader_experts.yaml")
    parser.add_argument("--data", required=True, help="Data root (with train/val subdirs)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", default=None)
    parser.add_argument("--framework", default="torch", help="(ignored, kept for CLI compat)")
    parser.add_argument("--tiny", action="store_true", help="Use SimpleCRNNTiny (~50K params)")
    parser.add_argument("--synth", default=None, help="Path to synth data dir (merged into train)")
    parser.add_argument("--finetune", default=None, help="Checkpoint to fine-tune from (stage 2)")
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

    # Vocab
    vocab = Vocab.from_config(args.expert)
    print(f"Vocab: {vocab}")
    vocab.save(output_dir / "vocab.txt")

    # Data
    train_ds = PriceReaderDataset(data_root / "train", vocab, augment=True)
    val_ds = PriceReaderDataset(data_root / "val", vocab, augment=False)

    # Merge synthetic data into training set
    if args.synth:
        synth_ds = PriceReaderDataset(Path(args.synth), vocab, augment=False)
        print(f"Synth: {len(synth_ds)} samples")
        train_ds = torch.utils.data.ConcatDataset([synth_ds, train_ds])

    print(f"Train: {len(train_ds)} samples, Val: {len(val_ds)} samples")

    if len(train_ds) == 0:
        print("ERROR: No training data. Run scripts/extract_price_crops.py first.")
        return

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=0, collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=0, collate_fn=collate_fn,
    )

    # Model
    if args.finetune:
        print(f"Fine-tuning from: {args.finetune}")
        checkpoint = torch.load(args.finetune, map_location=device, weights_only=False)
        model = checkpoint["model"].to(device)
    elif args.tiny:
        model = SimpleCRNNTiny(vocab_size=vocab.size).to(device)
    else:
        model = SimpleCRNN(vocab_size=vocab.size).to(device)
    print(f"{model.__class__.__name__} parameters: {count_parameters(model):,}")

    criterion = nn.CTCLoss(blank=vocab.blank_idx, zero_infinity=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # Training loop
    best_field_acc = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_metrics = evaluate(model, val_loader, criterion, vocab, device)
        scheduler.step()
        elapsed = time.time() - t0

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_metrics["loss"],
            "val_char_acc": val_metrics["char_acc"],
            "val_field_acc": val_metrics["field_acc"],
        })

        print(
            f"Epoch {epoch:3d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} "
            f"char_acc={val_metrics['char_acc']:.3f} "
            f"field_acc={val_metrics['field_acc']:.3f} | "
            f"{elapsed:.1f}s"
        )

        if val_metrics["field_acc"] > best_field_acc:
            best_field_acc = val_metrics["field_acc"]
            torch.save({
                "model": model,
                "model_state_dict": model.state_dict(),
                "epoch": epoch,
                "val_field_acc": val_metrics["field_acc"],
                "val_char_acc": val_metrics["char_acc"],
                "vocab_size": vocab.size,
                "charset": vocab.charset,
            }, output_dir / "best.pt")
            print(f"  -> Saved best model (field_acc={val_metrics['field_acc']:.3f})")

    # Save final
    torch.save({
        "model": model,
        "model_state_dict": model.state_dict(),
        "epoch": args.epochs,
        "val_field_acc": val_metrics["field_acc"],
        "val_char_acc": val_metrics["char_acc"],
        "vocab_size": vocab.size,
        "charset": vocab.charset,
    }, output_dir / "last.pt")

    # Save history
    with open(output_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nBest val field accuracy: {best_field_acc:.3f}")
    print(f"Model saved to: {output_dir}")


if __name__ == "__main__":
    main()
