"""Tests for fuel price generation."""

from au_fuel_sign_ocr_factory.synth.price_generator import (
    format_price,
    generate_correlated_prices,
    generate_price,
    load_fuel_types,
)


def test_load_fuel_types():
    ft = load_fuel_types()
    assert "U91" in ft
    assert "DIESEL" in ft
    assert "LPG" in ft
    assert len(ft) == 8


def test_generate_price_in_range():
    ft = load_fuel_types()
    for key in ft:
        for _ in range(50):
            price = generate_price(key, fuel_types=ft)
            lo, hi = ft[key]["price_range"]
            assert lo <= price <= hi, f"{key}: {price} not in [{lo}, {hi}]"


def test_price_has_one_decimal():
    ft = load_fuel_types()
    for key in ft:
        price = generate_price(key, fuel_types=ft)
        # Check format: at most one decimal place
        s = f"{price:.1f}"
        assert float(s) == price


def test_correlated_prices_ordering():
    """E10 < U91 < P95 < P98 in most cases."""
    ft = load_fuel_types()
    keys = ["E10", "U91", "P95", "P98"]
    correct_order = 0
    trials = 100
    for _ in range(trials):
        prices = generate_correlated_prices(keys, fuel_types=ft)
        if prices["E10"] < prices["U91"] < prices["P95"] < prices["P98"]:
            correct_order += 1
    # Should maintain order in most cases (allow some randomness)
    assert correct_order > trials * 0.7, f"Only {correct_order}/{trials} in order"


def test_correlated_prices_lpg_cheapest():
    """LPG should be significantly cheaper than petrol."""
    ft = load_fuel_types()
    keys = ["U91", "LPG"]
    for _ in range(50):
        prices = generate_correlated_prices(keys, fuel_types=ft)
        assert prices["LPG"] < prices["U91"], f"LPG {prices['LPG']} >= U91 {prices['U91']}"


def test_format_price():
    assert format_price(189.9) == "189.9"
    assert format_price(89.0) == "89.0"
    assert format_price(200.5) == "200.5"
