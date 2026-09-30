# `analysis/features`

## Purpose

Computes a rolling VWAP per symbol over the last `window` trades of that symbol.

## Files

| File | What it holds |
|---|---|
| `vwap.py` | `VwapPoint`, `rolling_vwap` |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `VwapPoint` | frozen dataclass `(symbol, ts, vwap)` | no |
| `rolling_vwap` | `(trades: list[Trade], window: int) -> list[VwapPoint]` | no |

## Pipeline / workflow

Per trade, in input order: append it to its symbol's window (a `deque` of `window` trades),
then emit `sum(price * size) / sum(size)` over that window.

## Configuration

none.

## Running and testing

`uv run pytest packages/analysis/tests/intent/features packages/analysis/tests/unit/features`

## Implementation notes

`Trade` is imported from `data.ingest` while `data`'s surface is unbuilt (contract §6: the
name is provisional). The window is keyed by `symbol` only (contract §7: `window` counts
trades per symbol). No deviations recorded.
