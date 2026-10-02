"""The exchange's trading calendar for the `clean` section.

Entry point: `session_days`, the trading days in a window. The calendar is read once
from the file the package settings name and kept for the life of the process.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from data.configs import load_settings

_SATURDAY = 5


def session_days(start: date, end: date) -> list[date]:
    """Return the exchange's trading days from start to end, both included.

    Args:
        start: The first day of the window.
        end: The last day of the window.

    Returns:
        The trading days in the window, oldest first.
    """
    holidays = _Loader(load_settings().calendar_path).holidays()
    span = range((end - start).days + 1)
    days = [start + timedelta(days=offset) for offset in span]
    return [day for day in days if day.weekday() < _SATURDAY and day not in holidays]


class _Loader:
    """Reads the exchange's holiday file.

    Attributes:
        path: The JSON file of holiday dates, one ISO date per entry.
    """

    _cache: dict[Path, frozenset[date]] = {}

    def __init__(self, path: Path) -> None:
        """Initializes the loader for one holiday file.

        Args:
            path: The JSON file of holiday dates.
        """
        self.path = path

    def holidays(self) -> frozenset[date]:
        """Return the exchange's holidays, reading the file on the first call only."""
        if self.path not in self._cache:
            entries = json.loads(self.path.read_text())
            self._cache[self.path] = frozenset(date.fromisoformat(e) for e in entries)
        return self._cache[self.path]
