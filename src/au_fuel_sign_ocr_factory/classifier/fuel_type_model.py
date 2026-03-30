"""SimpleCNN for 8-class fuel type classification.

Input: RGB crop of the label region (left-of-price), resized to 48x128.
Output: one of 8 fuel types (U91, E10, P95, P98, Diesel, LPG, AdBlue, E85).

Architecture is deliberately tiny to fit within the 0.5 MB INT8 budget.
"""

from __future__ import annotations

import torch
import torch.nn as nn

FUEL_TYPES = ["U91", "E10", "P95", "P98", "Diesel", "LPG", "AdBlue", "E85"]
NUM_CLASSES = len(FUEL_TYPES)


class FuelTypeCNN(nn.Module):
    """Lightweight CNN classifier for fuel type labels.

    Input: (B, 3, 48, 128) — RGB label crop
    Output: (B, 8) — logits for each fuel type
    """

    def __init__(self, num_classes: int = NUM_CLASSES):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 3 → 16, 48x128 → 24x64
            nn.Conv2d(3, 16, 3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            # Block 2: 16 → 32, 24x64 → 12x32
            nn.Conv2d(16, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            # Block 3: 32 → 64, 12x32 → 6x16
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            # Block 4: 64 → 64, 6x16 → 3x8
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


if __name__ == "__main__":
    model = FuelTypeCNN()
    print(f"Parameters: {count_parameters(model):,}")
    print(f"Estimated size FP32: {count_parameters(model) * 4 / 1024 / 1024:.2f} MB")
    print(f"Estimated size INT8: {count_parameters(model) / 1024 / 1024:.2f} MB")

    # Test forward pass
    x = torch.randn(4, 3, 48, 128)
    y = model(x)
    print(f"Input:  {x.shape}")
    print(f"Output: {y.shape}")
    print(f"Classes: {FUEL_TYPES}")
