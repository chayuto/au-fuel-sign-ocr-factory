"""Model wrappers for inference pipeline.

Each model has a consistent interface: load from checkpoint, predict on a crop.
When no checkpoint is available, a stub mode returns dummy results for pipeline testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

# Fuel type enum for classifier output
FUEL_TYPES = ["U91", "E10", "P95", "P98", "Diesel", "LPG", "AdBlue", "E85"]
FUEL_TYPE_TO_IDX = {ft: i for i, ft in enumerate(FUEL_TYPES)}


# --- Protocols ---


class PriceReaderProtocol(Protocol):
    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        """Read price from crop. Returns (text, confidence)."""
        ...


class FuelTypeClassifierProtocol(Protocol):
    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        """Classify fuel type from crop. Returns (fuel_type, confidence)."""
        ...


class BrandClassifierProtocol(Protocol):
    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        """Classify brand from crop. Returns (brand, confidence)."""
        ...


# --- Stub implementations (for pipeline testing before models are trained) ---


class StubPriceReader:
    """Returns dummy price for pipeline testing."""

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        return "000.0", 0.0


class StubFuelTypeClassifier:
    """Returns dummy fuel type for pipeline testing."""

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        return "U91", 0.0


class StubBrandClassifier:
    """Returns dummy brand for pipeline testing."""

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        return "unknown", 0.0


# --- Real model wrappers (loaded from checkpoints) ---


class SimpleCRNNPriceReader:
    """CTC-based price reader using SimpleCRNN architecture.

    Loads a trained PyTorch checkpoint and runs inference on price crops.
    """

    def __init__(self, checkpoint_path: str | Path):
        import torch

        from au_fuel_sign_ocr_factory.reader.vocab import Vocab

        self.device = torch.device("cpu")
        self.vocab = Vocab.from_config("price")

        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.model = checkpoint["model"] if "model" in checkpoint else None
        if self.model is not None:
            self.model.eval()

        # Preprocessing params
        self.img_height = 48
        self.img_max_width = 320

    def _preprocess(self, crop: np.ndarray) -> "torch.Tensor":
        import cv2
        import torch

        # Resize to fixed height, variable width
        h, w = crop.shape[:2]
        new_w = min(self.img_max_width, int(w * self.img_height / h))
        resized = cv2.resize(crop, (new_w, self.img_height))
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
        # Normalize to [0, 1]
        tensor = torch.from_numpy(gray).float() / 255.0
        # Add batch and channel dims: 1 x 1 x H x W
        return tensor.unsqueeze(0).unsqueeze(0)

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        import torch

        if self.model is None:
            return "000.0", 0.0

        with torch.no_grad():
            x = self._preprocess(crop).to(self.device)
            logits = self.model(x)  # T x B x C
            probs = torch.softmax(logits, dim=-1)
            max_probs, indices = probs.max(dim=-1)  # T x B
            confidence = max_probs[:, 0].mean().item()
            text = self.vocab.ctc_decode(indices[:, 0].tolist())

        return text, confidence


class SimpleCNNFuelTypeClassifier:
    """8-class fuel type classifier.

    Loads a trained PyTorch checkpoint and runs inference on label region crops.
    """

    def __init__(self, checkpoint_path: str | Path):
        import torch

        self.device = torch.device("cpu")
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.model = checkpoint.get("model")
        if self.model is not None:
            self.model.eval()
        self.img_size = (48, 128)  # H x W

    def _preprocess(self, crop: np.ndarray) -> "torch.Tensor":
        import cv2
        import torch

        resized = cv2.resize(crop, (self.img_size[1], self.img_size[0]))
        if len(resized.shape) == 2:
            resized = np.stack([resized] * 3, axis=-1)
        # HWC → CHW, normalize
        tensor = torch.from_numpy(resized).float().permute(2, 0, 1) / 255.0
        return tensor.unsqueeze(0)

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        import torch

        if self.model is None:
            return "U91", 0.0

        with torch.no_grad():
            x = self._preprocess(crop).to(self.device)
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1)
            conf, idx = probs[0].max(dim=0)
            return FUEL_TYPES[idx.item()], conf.item()


class SimpleCNNBrandClassifier:
    """13-class brand classifier.

    Loads a trained PyTorch checkpoint and runs inference on sign_board crops.
    """

    BRANDS = [
        "shell", "bp", "ampol", "caltex", "seven_eleven", "united",
        "costco", "liberty", "puma", "metro", "mobil", "otr", "independent",
    ]

    def __init__(self, checkpoint_path: str | Path):
        import torch

        self.device = torch.device("cpu")
        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.model = checkpoint.get("model")
        if self.model is not None:
            self.model.eval()
        self.img_size = (128, 128)

    def _preprocess(self, crop: np.ndarray) -> "torch.Tensor":
        import cv2
        import torch

        resized = cv2.resize(crop, (self.img_size[1], self.img_size[0]))
        if len(resized.shape) == 2:
            resized = np.stack([resized] * 3, axis=-1)
        tensor = torch.from_numpy(resized).float().permute(2, 0, 1) / 255.0
        return tensor.unsqueeze(0)

    def predict(self, crop: np.ndarray) -> tuple[str, float]:
        import torch

        if self.model is None:
            return "unknown", 0.0

        with torch.no_grad():
            x = self._preprocess(crop).to(self.device)
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1)
            conf, idx = probs[0].max(dim=0)
            return self.BRANDS[idx.item()], conf.item()


# --- Factory ---


def load_price_reader(checkpoint: str | Path | None = None) -> PriceReaderProtocol:
    if checkpoint and Path(checkpoint).exists():
        return SimpleCRNNPriceReader(checkpoint)
    return StubPriceReader()


def load_fuel_type_classifier(checkpoint: str | Path | None = None) -> FuelTypeClassifierProtocol:
    if checkpoint and Path(checkpoint).exists():
        return SimpleCNNFuelTypeClassifier(checkpoint)
    return StubFuelTypeClassifier()


def load_brand_classifier(checkpoint: str | Path | None = None) -> BrandClassifierProtocol:
    if checkpoint and Path(checkpoint).exists():
        return SimpleCNNBrandClassifier(checkpoint)
    return StubBrandClassifier()
