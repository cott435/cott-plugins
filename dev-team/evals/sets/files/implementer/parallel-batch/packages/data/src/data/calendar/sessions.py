"""XVEN session rules: weekends and the venue's fixed holidays."""

from __future__ import annotations

import os
from datetime import date

HOLIDAYS: frozenset[tuple[int, int]] = frozenset({(1, 1), (12, 25), (12, 26)})


def is_session(day: date) -> bool:
    """True when XVEN trades on `day`."""
    return day.weekday() < 5 and (day.month, day.day) not in HOLIDAYS
