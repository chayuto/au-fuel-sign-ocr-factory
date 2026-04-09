"""Price Reader models — CTC-based and classification-based approaches.

Two architectures:
  1. SimpleCRNN / SimpleCRNNTiny — CTC-based, variable-length output
  2. PriceClassifier — fixed 5-position classification, no CTC alignment needed

Input for all: (B, 1, 48, W) grayscale image
"""

from __future__ import annotations

import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# CTC-based models (SimpleCRNN)
# ---------------------------------------------------------------------------

class SimpleCRNN(nn.Module):
    """CNN + BiLSTM + CTC for general OCR."""

    def __init__(self, vocab_size: int = 12, hidden_size: int = 128, num_lstm_layers: int = 2):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True), nn.MaxPool2d((2, 1)),
            nn.Conv2d(128, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.AdaptiveAvgPool2d((1, None)),
        )
        self.lstm = nn.LSTM(64, hidden_size, num_lstm_layers, bidirectional=True,
                            dropout=0.1 if num_lstm_layers > 1 else 0)
        self.fc = nn.Linear(hidden_size * 2, vocab_size)

    def forward(self, x):
        conv = self.cnn(x)
        seq = conv.squeeze(2).permute(2, 0, 1)
        out, _ = self.lstm(seq)
        return self.fc(out)


class SimpleCRNNTiny(nn.Module):
    """Smaller CRNN for low-data regime."""

    def __init__(self, vocab_size: int = 12, hidden_size: int = 64):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 16, 3, 1, 1), nn.BatchNorm2d(16), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True),
            nn.AdaptiveAvgPool2d((1, None)),
        )
        self.lstm = nn.LSTM(32, hidden_size, 1, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, vocab_size)

    def forward(self, x):
        conv = self.cnn(x)
        seq = conv.squeeze(2).permute(2, 0, 1)
        out, _ = self.lstm(seq)
        return self.fc(out)


# ---------------------------------------------------------------------------
# Classification-based model (PriceClassifier)
# ---------------------------------------------------------------------------

class PriceClassifier(nn.Module):
    """Fixed-position digit classification for price reading.

    Prices are always XX.X or XXX.X format → 5 character positions:
      pos 0: hundreds digit (0-9) or blank (11) for XX.X format
      pos 1: tens digit (0-9)
      pos 2: ones digit (0-9)
      pos 3: decimal point (always '.', not predicted)
      pos 4: tenths digit (0-9)

    4 classification heads, each 11 classes (0-9 + blank).
    No CTC alignment needed — just CNN → global features → 4 heads.

    ~85K params.
    """

    NUM_HEADS = 4  # positions 0, 1, 2, 4 (skip decimal)
    NUM_CLASSES = 11  # 0-9 + blank

    def __init__(self, dropout: float = 0.3):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1), nn.BatchNorm2d(32), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, 1, 1), nn.BatchNorm2d(128), nn.ReLU(True), nn.MaxPool2d(2, 2),
            nn.Conv2d(128, 64, 3, 1, 1), nn.BatchNorm2d(64), nn.ReLU(True),
            nn.AdaptiveAvgPool2d((1, 5)),  # 6xW → 1x5 (MPS-compatible)
        )

        feature_dim = 64 * 5  # 320
        self.dropout = nn.Dropout(dropout)

        # 4 independent heads
        self.heads = nn.ModuleList([
            nn.Linear(feature_dim, self.NUM_CLASSES) for _ in range(self.NUM_HEADS)
        ])

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        """Returns list of 4 logit tensors, each (B, 11)."""
        features = self.cnn(x)  # (B, 64, 1, 8)
        features = features.view(features.size(0), -1)  # (B, 512)
        features = self.dropout(features)
        return [head(features) for head in self.heads]

    def decode(self, logits_list: list[torch.Tensor]) -> list[str]:
        """Decode batch of predictions to price strings."""
        batch_size = logits_list[0].size(0)
        results = []
        for b in range(batch_size):
            chars = []
            for i, logits in enumerate(logits_list):
                idx = logits[b].argmax().item()
                if idx == 10:  # blank
                    continue
                chars.append(str(idx))
                if i == 2:  # after ones digit, insert decimal point
                    chars.append('.')
            results.append(''.join(chars))
        return results


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
