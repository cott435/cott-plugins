"""Load one account's bars for one trading day from the vendor into the `bars` table.

Entry point: `load_account`. In the repo this module is `src/data/ingest/load.py`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from sqlite3 import Connection

from loguru import logger

from data.clean.calendar import Calendar
from data.ingest.models import LoadSummary
from data.vendor import VendorClient, VendorTimeout

_MAX_ATTEMPTS = 3


def load_account(
    conn: Connection,
    client: VendorClient,
    account: str,
    day: date,
    calendar: Calendar,
    batch_size: int,
    overwrite: bool,
) -> LoadSummary:
    """Download one account's bars for one day, write them to `bars`, record the load.

    A day already in `load_ledger` is skipped unless `overwrite` is set, in which case
    its bars and its ledger row are replaced.

    Args:
        conn: An open connection to the package database.
        client: The vendor client the bars are downloaded with.
        account: The vendor's account identifier.
        day: The trading day to load.
        calendar: The exchange calendar that gives the day's session.
        batch_size: The most rows written in one transaction.
        overwrite: Reload a day that is already in the ledger.

    Returns:
        The rows written, the rows dropped and whether the day was skipped.

    Raises:
        ValueError: `batch_size` is below one, or `day` has no session.
        VendorTimeout: A page timed out on every attempt.
    """
    # Refuse inputs that cannot produce a load.
    if batch_size < 1:
        raise ValueError(f"batch_size must be at least 1, got {batch_size}")
    if not calendar.is_session(day):
        raise ValueError(f"{day} is not a trading day")

    # Skip a day the ledger already has, or clear it when asked to overwrite.
    loaded = conn.execute(
        "SELECT row_count FROM load_ledger WHERE account = ? AND day = ?",
        (account, day.isoformat()),
    ).fetchone()
    if loaded is not None and not overwrite:
        logger.info("{} {} already loaded, skipping", account, day)
        return LoadSummary(
            account=account, day=day, rows=loaded[0], dropped=0, skipped=True
        )
    if loaded is not None:
        conn.execute(
            "DELETE FROM bars WHERE account = ? AND day = ?", (account, day.isoformat())
        )
        conn.execute(
            "DELETE FROM load_ledger WHERE account = ? AND day = ?",
            (account, day.isoformat()),
        )
        conn.commit()

    # Download the day page by page; a page that times out is asked for again.
    raw: list[dict[str, float | int]] = []
    cursor: str | None = None
    while True:
        attempt = 0
        while True:
            try:
                page = client.download(account, day, cursor=cursor)
                break
            except VendorTimeout:
                attempt += 1
                if attempt >= _MAX_ATTEMPTS:
                    raise
                logger.warning(
                    "{} {} page timed out, attempt {}", account, day, attempt
                )
        raw.extend(page.rows)
        cursor = page.next_cursor
        if cursor is None:
            break
    if not raw:
        logger.warning("{} {} vendor returned no rows", account, day)

    # Turn the vendor's rows into bars in exchange time; drop any outside the session.
    session_open, session_close = calendar.session(day)
    bars: list[tuple[str, str, str, float, float, float, float, int]] = []
    dropped = 0
    for row in raw:
        stamp = datetime.fromtimestamp(row["t"] / 1000, tz=UTC).astimezone(calendar.tz)
        if stamp < session_open or stamp >= session_close:
            dropped += 1
            continue
        if row["v"] < 0:
            logger.debug("{} {} negative volume at {}", account, day, stamp)
            dropped += 1
            continue
        scale = 10 ** row.get("scale", 0)
        bars.append(
            (
                account,
                day.isoformat(),
                stamp.isoformat(),
                row["o"] / scale,
                row["h"] / scale,
                row["l"] / scale,
                row["c"] / scale,
                int(row["v"]),
            )
        )

    # The vendor repeats a bar it has revised: keep the last version of each timestamp.
    latest: dict[str, tuple[str, str, str, float, float, float, float, int]] = {}
    for bar in bars:
        latest[bar[2]] = bar
    revised = len(bars) - len(latest)
    if revised:
        logger.debug("{} {} vendor revised {} bars", account, day, revised)
    dropped += revised
    bars = sorted(latest.values(), key=lambda bar: bar[2])

    # Write in batches so one transaction never holds more than batch_size rows.
    written = 0
    for offset in range(0, len(bars), batch_size):
        batch = bars[offset : offset + batch_size]
        conn.executemany(
            "INSERT INTO bars (account, day, stamp, open, high, low, close, volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            batch,
        )
        conn.commit()
        written += len(batch)
        logger.debug("{} {} wrote {} of {} bars", account, day, written, len(bars))

    # Record the load so the next run skips this day.
    conn.execute(
        "INSERT INTO load_ledger (account, day, row_count, loaded_at) "
        "VALUES (?, ?, ?, ?)",
        (account, day.isoformat(), written, datetime.now(tz=UTC).isoformat()),
    )
    conn.commit()
    if dropped:
        logger.warning("{} {} dropped {} bars", account, day, dropped)
    logger.info("{} {} loaded {} bars", account, day, written)
    return LoadSummary(
        account=account, day=day, rows=written, dropped=dropped, skipped=False
    )
