"""Generate fuel entry combinations for synthetic sign rendering.

Selects which fuel types appear on a sign and which display text alias to use.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

from au_fuel_sign_ocr_factory.annotate.schema import FuelType
from au_fuel_sign_ocr_factory.synth.price_generator import (
    generate_correlated_prices,
    load_fuel_types,
)

_CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


def load_brands() -> dict:
    """Load brand definitions from config."""
    with open(_CONFIGS_DIR / "brands.yaml") as f:
        return yaml.safe_load(f)["brands"]


def pick_fuel_selection(
    brand_key: str | None = None,
    brands: dict | None = None,
    fuel_types: dict | None = None,
    min_entries: int = 3,
    max_entries: int = 6,
) -> list[str]:
    """Pick which fuel types appear on a sign.

    If a brand is specified, uses its common_fuels as the pool.
    Otherwise picks from all fuel types.

    Returns:
        List of fuel type keys (e.g., ["E10", "U91", "P95", "P98", "DIESEL"]).
    """
    if fuel_types is None:
        fuel_types = load_fuel_types()

    pool: list[str]
    if brand_key and brands:
        pool = list(brands[brand_key].get("common_fuels", fuel_types.keys()))
    else:
        pool = list(fuel_types.keys())

    n = random.randint(min_entries, min(max_entries, len(pool)))
    # Weighted selection: common fuels more likely
    common = ["U91", "E10", "P95", "P98", "DIESEL"]
    # Ensure at least one common fuel is included
    selected = []
    common_in_pool = [f for f in common if f in pool]
    if common_in_pool:
        selected.append(random.choice(common_in_pool))

    remaining = [f for f in pool if f not in selected]
    random.shuffle(remaining)
    selected.extend(remaining[: n - len(selected)])

    # Sort in conventional display order
    display_order = ["E10", "U91", "P95", "P98", "DIESEL", "LPG", "ADBLUE", "E85"]
    selected.sort(key=lambda x: display_order.index(x) if x in display_order else 99)
    return selected


def pick_display_text(fuel_type_key: str, fuel_types: dict | None = None) -> str:
    """Pick a random display text alias for a fuel type.

    Args:
        fuel_type_key: Canonical key (e.g., "U91").
        fuel_types: Pre-loaded fuel types dict.

    Returns:
        Display string as it would appear on a sign (e.g., "Unleaded 91").
    """
    if fuel_types is None:
        fuel_types = load_fuel_types()

    aliases = fuel_types[fuel_type_key]["aliases"]
    return random.choice(aliases).upper()


def generate_sign_entries(
    brand_key: str | None = None,
    brands: dict | None = None,
    fuel_types: dict | None = None,
    min_entries: int = 3,
    max_entries: int = 6,
) -> list[dict]:
    """Generate a complete set of fuel entries for one sign.

    Returns:
        List of dicts with keys: fuel_type, display_text, price.
        Bounding boxes are NOT included (added during rendering).
    """
    if fuel_types is None:
        fuel_types = load_fuel_types()
    if brands is None:
        brands = load_brands()

    fuel_keys = pick_fuel_selection(
        brand_key=brand_key,
        brands=brands,
        fuel_types=fuel_types,
        min_entries=min_entries,
        max_entries=max_entries,
    )
    prices = generate_correlated_prices(fuel_keys, fuel_types=fuel_types)

    entries = []
    for key in fuel_keys:
        entries.append({
            "fuel_type": FuelType(fuel_types[key]["canonical"]),
            "display_text": pick_display_text(key, fuel_types=fuel_types),
            "price": prices[key],
        })
    return entries
