"""Tests for fuel type enum and entry generation."""

from au_fuel_sign_ocr_factory.annotate.schema import FuelType
from au_fuel_sign_ocr_factory.synth.fuel_entries import (
    generate_sign_entries,
    load_brands,
    pick_display_text,
    pick_fuel_selection,
)
from au_fuel_sign_ocr_factory.synth.price_generator import load_fuel_types


def test_fuel_type_enum_matches_config():
    """Enum values must match config canonical names."""
    ft = load_fuel_types()
    for key, info in ft.items():
        canonical = info["canonical"]
        assert FuelType(canonical), f"FuelType missing: {canonical}"


def test_pick_fuel_selection_count():
    ft = load_fuel_types()
    brands = load_brands()
    for _ in range(50):
        selected = pick_fuel_selection(fuel_types=ft, min_entries=3, max_entries=6)
        assert 3 <= len(selected) <= 6


def test_pick_fuel_selection_brand_constrained():
    ft = load_fuel_types()
    brands = load_brands()
    selected = pick_fuel_selection(
        brand_key="costco", brands=brands, fuel_types=ft
    )
    # Costco only has U91, P95, DIESEL
    costco_fuels = set(brands["costco"]["common_fuels"])
    for fuel in selected:
        assert fuel in costco_fuels, f"{fuel} not in Costco's fuel list"


def test_pick_display_text_uppercase():
    ft = load_fuel_types()
    for key in ft:
        for _ in range(10):
            text = pick_display_text(key, fuel_types=ft)
            assert text == text.upper(), f"Display text not uppercase: {text}"


def test_generate_sign_entries():
    entries = generate_sign_entries(min_entries=3, max_entries=5)
    assert 3 <= len(entries) <= 5
    for entry in entries:
        assert isinstance(entry["fuel_type"], FuelType)
        assert isinstance(entry["display_text"], str)
        assert isinstance(entry["price"], float)
        assert entry["price"] > 0


def test_generate_sign_entries_with_brand():
    brands = load_brands()
    ft = load_fuel_types()
    entries = generate_sign_entries(brand_key="shell", brands=brands, fuel_types=ft)
    assert len(entries) >= 3
    shell_fuels = set(brands["shell"]["common_fuels"])
    for entry in entries:
        # The fuel type canonical name should map back to a valid key
        key = next(
            k for k, v in ft.items() if v["canonical"] == entry["fuel_type"].value
        )
        assert key in shell_fuels
