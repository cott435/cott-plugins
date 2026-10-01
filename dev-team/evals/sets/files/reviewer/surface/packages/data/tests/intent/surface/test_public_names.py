"""Intent tests for the package's public names (design §5, §6)."""

import pytest

import data


def test_all_is_the_public_names():
    """Design §5: `__all__` is exactly the `Public: yes` names."""
    assert sorted(data.__all__) == ["clean_bars", "fetch_bars"]


def test_public_names_resolve_to_callables():
    """Design §5 fetch_bars, clean_bars: both are re-exported from `data`."""
    assert callable(data.fetch_bars)
    assert callable(data.clean_bars)


def test_unknown_name_raises_attribute_error():
    """Design §6 a name `data` does not export: AttributeError."""
    name = "trading_days"
    with pytest.raises(AttributeError):
        getattr(data, name)
