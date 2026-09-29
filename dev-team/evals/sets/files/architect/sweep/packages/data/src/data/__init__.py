"""data — the trade tape's ingest, clean and storage package.

Public surface per docs/packages/data/interface.md; section modules are imported lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data.errors import DataError, TradeParseError

if TYPE_CHECKING:
    from data.ingest.model import Trade
    from data.storage.db import load_trades

__all__ = ["DataError", "Trade", "TradeParseError", "load_trades"]


def __getattr__(name: str):  # noqa: ANN202 — lazy surface
    if name == "Trade":
        from data.ingest.model import Trade

        return Trade
    if name == "load_trades":
        from data.storage.db import load_trades

        return load_trades
    raise AttributeError(name)
