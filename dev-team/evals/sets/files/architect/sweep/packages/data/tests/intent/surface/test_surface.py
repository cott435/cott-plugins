"""Intent tests for data/surface."""

import data


def test_public_names():
    """Design §5 Public names: __all__ matches interface.md."""
    assert set(data.__all__) == {"DataError", "Trade", "TradeParseError", "load_trades"}
