# `data/clean`

Built 2026-09-28. Run: `run-package data`.

## Purpose

Turns the rows `ingest` reads into a **TradeTable**: exact duplicate rows collapse to one and
the result is sorted by `ts` then `symbol`. No parsing, no persistence.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `rules.py` | `clean_trades`, `CleanError`, the dedupe key and the dedupe | the `daily` pipeline |
| `__init__.py` | re-exports `clean_trades` and `CleanError` | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `clean_trades` | `(rows: list[Trade]) -> list[Trade]` | dedupe and sort one day's rows; the input is not mutated | no |
| `CleanError` | `class CleanError(ValueError)` | reserved for a naive `ts` after ingest | no |

## Pipeline / workflow

`clean_trades(rows)` → `_dedupe` (one row per five-field key, first occurrence kept) → a
stable sort by `(ts, symbol)` → `list[Trade]`. Second step of the `daily` pipeline.

## Configuration

None.

## Running and testing

`uv run pytest packages/data/tests/unit/clean packages/data/tests/intent/clean`

## Implementation notes

- `Trade` is unhashable (the ingest README), so the dedupe key is the tuple of its five
  fields, not the row itself.
- Dependencies consumed: `data/ingest` (`Trade`). Decisions applied: none.
