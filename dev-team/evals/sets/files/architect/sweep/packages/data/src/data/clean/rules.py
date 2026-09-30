"""Dedupe and sort Trade records."""

from __future__ import annotations

import logging

from data.ingest.model import Trade

log = logging.getLogger(__name__)


def dedupe(trades: list[Trade]) -> tuple[list[Trade], int]:
    """Drop records equal on all five fields, keeping the first; return (kept, dropped).

    The dropped count is returned so the pipeline can log it — docs/deviations.md,
    data/clean — 2026-09-24 (approved).
    """
    seen: set[Trade] = set()
    kept: list[Trade] = []
    for trade in trades:
        if trade in seen:
            continue
        seen.add(trade)
        kept.append(trade)
    dropped = len(trades) - len(kept)
    log.info("dropped %d duplicate trades", dropped)
    return kept, dropped


def sort_by_ts(trades: list[Trade]) -> list[Trade]:
    """Stable ascending sort by ts."""
    return sorted(trades, key=lambda t: t.ts)


def clean_trades(trades: list[Trade]) -> list[Trade]:
    """sort_by_ts(dedupe(trades)[0])."""
    kept, _dropped = dedupe(trades)
    return sort_by_ts(kept)
