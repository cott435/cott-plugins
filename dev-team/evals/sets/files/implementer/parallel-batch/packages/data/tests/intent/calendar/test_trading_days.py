"""Intent tests for `trading_days` — Design §5, one per stated behavior."""

from __future__ import annotations

from datetime import date

from data.calendar import trading_days


def test_weekends_are_not_trading_days() -> None:
    """Design §5 trading_days: Saturdays and Sundays are never returned."""
    days = trading_days(date(2026, 9, 25), date(2026, 9, 28))
    assert days == [date(2026, 9, 25), date(2026, 9, 28)]


def test_fixed_holidays_are_not_trading_days() -> None:
    """Design §5 trading_days: 25 and 26 December are never returned."""
    assert trading_days(date(2026, 12, 24), date(2026, 12, 28)) == [
        date(2026, 12, 24),
        date(2026, 12, 28),
    ]
