"""Tests for spatial label-to-price pairing."""

from au_fuel_sign_ocr_factory.annotate.schema import BBox
from au_fuel_sign_ocr_factory.utils.pairing import pair_labels_to_prices


def test_simple_three_row_pairing():
    """Three rows, labels on left, prices on right, same Y."""
    labels = [
        BBox(0.05, 0.20, 0.35, 0.30),  # row 1
        BBox(0.05, 0.40, 0.35, 0.50),  # row 2
        BBox(0.05, 0.60, 0.35, 0.70),  # row 3
    ]
    prices = [
        BBox(0.60, 0.20, 0.90, 0.30),  # row 1
        BBox(0.60, 0.40, 0.90, 0.50),  # row 2
        BBox(0.60, 0.60, 0.90, 0.70),  # row 3
    ]
    pairs = pair_labels_to_prices(labels, prices)
    assert pairs == [(0, 0), (1, 1), (2, 2)]


def test_shuffled_prices():
    """Prices in different order than labels — still pairs by Y."""
    labels = [
        BBox(0.05, 0.20, 0.35, 0.30),
        BBox(0.05, 0.50, 0.35, 0.60),
    ]
    prices = [
        BBox(0.60, 0.50, 0.90, 0.60),  # matches label[1]
        BBox(0.60, 0.20, 0.90, 0.30),  # matches label[0]
    ]
    pairs = pair_labels_to_prices(labels, prices)
    # Sorted by Y: label[0]->price[1], label[1]->price[0]
    assert pairs == [(0, 1), (1, 0)]


def test_no_match_beyond_threshold():
    """Labels and prices too far apart in Y."""
    labels = [BBox(0.05, 0.10, 0.35, 0.20)]
    prices = [BBox(0.60, 0.80, 0.90, 0.90)]
    pairs = pair_labels_to_prices(labels, prices, y_threshold=0.05)
    assert pairs == []


def test_empty_inputs():
    assert pair_labels_to_prices([], []) == []
    assert pair_labels_to_prices([BBox(0, 0, 1, 1)], []) == []
    assert pair_labels_to_prices([], [BBox(0, 0, 1, 1)]) == []


def test_label_must_be_left_of_price():
    """If label is to the right of price, no match."""
    labels = [BBox(0.70, 0.20, 0.95, 0.30)]  # right side
    prices = [BBox(0.05, 0.20, 0.30, 0.30)]  # left side
    pairs = pair_labels_to_prices(labels, prices)
    assert pairs == []
