# `data/clean`

Built 2026-09-28. Run: `run-package data`.

## Purpose

Turns the rows `ingest` returns into a **TradeTable**: every symbol in its canonical form,
sorted by `ts` then `symbol`. The rows arrive with their repeats already dropped; nothing is
deduplicated here. No parsing, no persistence.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `rules.py` | `normalise_symbol`, `clean_trades`, `CleanError` | the `daily` pipeline |
| `__init__.py` | re-exports the three names above | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `normalise_symbol` | `(raw: str) -> str` | the canonical form of a symbol, stripped and upper-case; the pipeline also hands it to `load_trades` for the dedupe key | no |
| `clean_trades` | `(rows: list[Trade]) -> list[Trade]` | normalise and sort one day's rows; the input is not mutated | no |
| `CleanError` | `class CleanError(ValueError)` | reserved for a naive `ts` after ingest | no |

## Pipeline / workflow

`clean_trades(rows)` → each row copied with `normalise_symbol(symbol)` → a stable sort by
`(ts, symbol)` → `list[Trade]`. Second step of the `daily` pipeline.

## Configuration

None.

## Running and testing

`uv run pytest packages/data/tests/unit/clean packages/data/tests/intent/clean`

## Implementation notes

- `normalise_symbol` is the package's one definition of a canonical symbol (contract, Package
  conventions).
- Rows are copied with `dataclasses.replace`, so the caller's rows keep their symbols as read.
- Dependencies consumed: `data/ingest` (`Trade`). Decisions applied: none.
