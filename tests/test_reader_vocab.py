"""Tests for reader vocabulary and CTC decode."""

from au_fuel_sign_ocr_factory.reader.vocab import Vocab


def test_price_vocab_from_config():
    v = Vocab.from_config("price")
    assert v.charset == "0123456789."
    assert v.size == 12  # 11 chars + blank
    assert v.blank_idx == 0


def test_label_vocab_from_config():
    v = Vocab.from_config("label")
    assert "A" in v.charset
    assert "Z" in v.charset
    assert "0" in v.charset
    assert " " in v.charset
    assert v.size == 43  # 42 chars + blank


def test_encode_decode_roundtrip():
    v = Vocab("0123456789.")
    text = "189.9"
    encoded = v.encode(text)
    decoded = v.decode(encoded)
    assert decoded == text


def test_ctc_decode_collapses_repeats():
    v = Vocab("0123456789.")
    # Simulate CTC output: 1,1,8,8,8,0,9,9,0,.,0,9
    # (0 = blank in CTC)
    indices = [1, 1, 2, 2, 2, 0, 3, 3, 0, 11, 0, 3]
    # char mapping: 0=blank, 1='0', 2='1', 3='2', ..., 11='.'
    # Wait, let me recalculate. charset = "0123456789."
    # idx 0 = blank, idx 1 = '0', idx 2 = '1', idx 3 = '2', ..., idx 10 = '9', idx 11 = '.'
    # For "189.9": '1'=idx2, '8'=idx9, '9'=idx10, '.'=idx11, '9'=idx10
    indices = [2, 2, 9, 9, 9, 0, 10, 10, 0, 11, 0, 10]
    result = v.ctc_decode(indices)
    assert result == "189.9"


def test_ctc_decode_handles_blanks():
    v = Vocab("0123456789.")
    # All blanks
    assert v.ctc_decode([0, 0, 0]) == ""
    # Single char surrounded by blanks
    assert v.ctc_decode([0, 2, 0]) == "1"


def test_encode_skips_unknown_chars():
    v = Vocab("0123456789.")
    encoded = v.encode("$189.9!")
    decoded = v.decode(encoded)
    assert decoded == "189.9"
