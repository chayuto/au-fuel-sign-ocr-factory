"""Annotation schema for Australian fuel sign OCR.

Each image contains one sign with multiple fuel entries (rows).
Bounding boxes are normalized [0, 1] relative to image dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FuelType(str, Enum):
    """Closed enum of Australian fuel types."""

    U91 = "U91"
    E10 = "E10"
    P95 = "P95"
    P98 = "P98"
    DIESEL = "Diesel"
    LPG = "LPG"
    ADBLUE = "AdBlue"
    E85 = "E85"


class SignType(str, Enum):
    """Physical sign display technology."""

    LED = "led"
    MECHANICAL = "mechanical"
    BACKLIT = "backlit"
    DIGITAL = "digital"


class TimeOfDay(str, Enum):
    DAY = "day"
    NIGHT = "night"
    DUSK = "dusk"


class Weather(str, Enum):
    CLEAR = "clear"
    OVERCAST = "overcast"
    RAIN = "rain"


class ImageSource(str, Enum):
    MANUAL = "manual"
    STREETVIEW = "streetview"
    WEB = "web"
    SYNTHETIC = "synthetic"


@dataclass
class BBox:
    """Normalized bounding box [0, 1] as (x1, y1, x2, y2)."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def w(self) -> float:
        return self.x2 - self.x1

    @property
    def h(self) -> float:
        return self.y2 - self.y1

    def to_yolo(self) -> tuple[float, float, float, float]:
        """Convert to YOLO format (cx, cy, w, h) normalized."""
        return (self.cx, self.cy, self.w, self.h)

    def to_list(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    @classmethod
    def from_yolo(cls, cx: float, cy: float, w: float, h: float) -> BBox:
        return cls(
            x1=cx - w / 2,
            y1=cy - h / 2,
            x2=cx + w / 2,
            y2=cy + h / 2,
        )


@dataclass
class FuelEntry:
    """A single fuel row on a sign: fuel type + price with bounding boxes."""

    fuel_type: FuelType
    display_text: str  # actual text on sign, e.g. "UNLEADED 91"
    price: float  # cents per litre, e.g. 189.9
    label_bbox: BBox
    price_bbox: BBox

    def to_dict(self) -> dict:
        return {
            "fuel_type": self.fuel_type.value,
            "display_text": self.display_text,
            "price": self.price,
            "label_bbox": self.label_bbox.to_list(),
            "price_bbox": self.price_bbox.to_list(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> FuelEntry:
        return cls(
            fuel_type=FuelType(d["fuel_type"]),
            display_text=d["display_text"],
            price=d["price"],
            label_bbox=BBox(*d["label_bbox"]),
            price_bbox=BBox(*d["price_bbox"]),
        )


@dataclass
class Conditions:
    """Capture conditions metadata."""

    time_of_day: TimeOfDay = TimeOfDay.DAY
    weather: Weather = Weather.CLEAR

    def to_dict(self) -> dict:
        return {
            "time_of_day": self.time_of_day.value,
            "weather": self.weather.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Conditions:
        return cls(
            time_of_day=TimeOfDay(d.get("time_of_day", "day")),
            weather=Weather(d.get("weather", "clear")),
        )


@dataclass
class FuelSignAnnotation:
    """Full annotation for one fuel sign image.

    Each image contains one sign with 3-6 fuel entry rows.
    """

    file: str
    source: ImageSource
    brand: str  # brand key from brands.yaml
    sign_type: SignType
    sign_bbox: BBox
    entries: list[FuelEntry] = field(default_factory=list)
    conditions: Conditions = field(default_factory=Conditions)
    brand_bbox: Optional[BBox] = None

    @property
    def num_entries(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        d = {
            "image": {
                "file": self.file,
                "source": self.source.value,
                "conditions": self.conditions.to_dict(),
            },
            "sign": {
                "bbox": self.sign_bbox.to_list(),
                "brand": self.brand,
                "sign_type": self.sign_type.value,
            },
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.brand_bbox is not None:
            d["sign"]["brand_bbox"] = self.brand_bbox.to_list()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> FuelSignAnnotation:
        img = d["image"]
        sign = d["sign"]
        return cls(
            file=img["file"],
            source=ImageSource(img["source"]),
            brand=sign["brand"],
            sign_type=SignType(sign["sign_type"]),
            sign_bbox=BBox(*sign["bbox"]),
            entries=[FuelEntry.from_dict(e) for e in d.get("entries", [])],
            conditions=Conditions.from_dict(img.get("conditions", {})),
            brand_bbox=BBox(*sign["brand_bbox"]) if "brand_bbox" in sign else None,
        )

    def to_yolo_labels(self) -> list[str]:
        """Convert annotation to YOLO label lines.

        Returns one line per detection: class_id cx cy w h
        Class mapping: 0=sign_board, 1=brand_zone, 2=fuel_label, 3=fuel_price
        """
        lines = []
        # Sign board (class 0)
        cx, cy, w, h = self.sign_bbox.to_yolo()
        lines.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        # Brand zone (class 1)
        if self.brand_bbox is not None:
            cx, cy, w, h = self.brand_bbox.to_yolo()
            lines.append(f"1 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        # Fuel entries
        for entry in self.entries:
            # Fuel label (class 2)
            cx, cy, w, h = entry.label_bbox.to_yolo()
            lines.append(f"2 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            # Fuel price (class 3)
            cx, cy, w, h = entry.price_bbox.to_yolo()
            lines.append(f"3 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        return lines
