from __future__ import annotations

from datetime import date
from sqlite3 import Connection

from loguru import logger

from data.clean.calendar import session_days
from data.ingest.fetch import fetch_day
from data.ingest.models import Bar
from data.vendor import VendorClient


def load_account(
    conn: Connection, client: VendorClient, account: str, *, start: date, end: date
) -> list[Bar]:
    days = _pending_days(conn, account, session_days(start, end))
    loader = _Loader(conn, client, account)
    bars = loader.run(days)
    logger.info("{} loaded {} bars over {} days", account, len(bars), len(days))
    return bars


def _pending_days(conn: Connection, account: str, days: list[date]) -> list[date]:
    rows = conn.execute("SELECT day FROM load_ledger WHERE account = ?", (account,))
    done = {row[0] for row in rows}
    return [day for day in days if day.isoformat() not in done]


class _Loader:
    def __init__(self, conn: Connection, client: VendorClient, account: str) -> None:
        self._conn = conn
        self._client = client
        self._account = account

    def run(self, days: list[date]) -> list[Bar]:
        bars: list[Bar] = []
        for day in days:
            day_bars = fetch_day(self._client, self._account, day)
            self._log_day(day, len(day_bars))
            bars.extend(day_bars)
        return bars

    def _log_day(self, day: date, bar_count: int) -> None:
        log_row = (self._account, day.isoformat(), bar_count)
        self._conn.execute(
            "INSERT INTO load_ledger (account, day, bar_count, loaded_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            log_row,
        )
        self._conn.commit()
