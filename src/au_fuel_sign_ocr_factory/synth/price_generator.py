"""Generate realistic Australian fuel prices.

Prices are in cents per litre with one decimal place (XXX.X format).
Ranges are calibrated to typical Australian fuel market conditions.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

_CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


def load_fuel_types() -> dict:
    """Load fuel type definitions from config."""
    with open(_CONFIGS_DIR / "fuel_types.yaml") as f:
        return yaml.safe_load(f)["fuel_types"]


def generate_price(fuel_type_key: str, fuel_types: dict | None = None) -> float:
    """Generate a realistic price for a given fuel type.

    Args:
        fuel_type_key: Canonical fuel type key (e.g., "U91", "DIESEL").
        fuel_types: Pre-loaded fuel types dict. Loaded from config if None.

    Returns:
        Price in cents per litre, one decimal place (e.g., 189.9).
    """
    if fuel_types is None:
        fuel_types = load_fuel_types()

    ft = fuel_types[fuel_type_key]
    lo, hi = ft["price_range"]
    # Generate price with .X decimal (tenths of a cent)
    price = random.uniform(lo, hi)
    return round(price, 1)


def generate_correlated_prices(
    fuel_type_keys: list[str],
    fuel_types: dict | None = None,
) -> dict[str, float]:
    """Generate a set of correlated fuel prices for one sign.

    Prices maintain realistic relative ordering:
    E10 < U91 < P95 < P98, LPG is cheapest, Diesel independent.

    Args:
        fuel_type_keys: List of fuel type keys to generate prices for.
        fuel_types: Pre-loaded fuel types dict. Loaded from config if None.

    Returns:
        Dict mapping fuel type key to price.
    """
    if fuel_types is None:
        fuel_types = load_fuel_types()

    # Generate base petrol price (U91 equivalent)
    u91_range = fuel_types["U91"]["price_range"]
    base_price = random.uniform(u91_range[0], u91_range[1])

    # Relative offsets from base (typical AU market spreads)
    offsets = {
        "E10": random.uniform(-8.0, -2.0),   # E10 is cheaper than U91
        "U91": 0.0,
        "P95": random.uniform(10.0, 25.0),    # Premium 95 markup
        "P98": random.uniform(20.0, 40.0),    # Premium 98 markup
        "DIESEL": random.uniform(-10.0, 20.0),  # Diesel varies independently
        "LPG": -(base_price * random.uniform(0.45, 0.60)),  # LPG ~40-55% of petrol
        "ADBLUE": -(base_price * random.uniform(0.40, 0.65)),  # AdBlue is cheap
        "E85": random.uniform(-30.0, -10.0),  # E85 cheaper than U91
    }

    prices = {}
    for key in fuel_type_keys:
        offset = offsets.get(key, 0.0)
        price = base_price + offset
        # Clamp to valid range
        lo, hi = fuel_types[key]["price_range"]
        price = max(lo, min(hi, price))
        prices[key] = round(price, 1)

    return prices


def format_price(price: float) -> str:
    """Format price for display on sign (e.g., 189.9)."""
    return f"{price:.1f}"
