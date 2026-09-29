"""Unit tests for analysis/features/vwap.py."""

from analysis.features.vwap import rolling_vwap


def test_empty_tape():
    assert rolling_vwap([], 3) == []
