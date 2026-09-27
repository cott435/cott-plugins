# `data/clean`

Shipped 2026-09-25, rewritten 2026-09-26 (fix round). Run: `run-package data`.

## Purpose

Collapses exact duplicate rows and sorts by `ts` then `symbol`, producing the **TradeTable**
shape together with the count of rows it dropped.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `rules.py` | `clean_trades`, `CleanResult`, `CleanError`, `_dedupe`, `_key` | `storage`, the `daily` pipeline |
| `__init__.py` | re-exports the three public names | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `clean_trades` | `(rows: list[Trade]) -> CleanResult` | dedupe and sort one batch; raises `CleanError` on a naive `ts` | no |
| `CleanResult` | `@dataclass(frozen=True, slots=True)` — `rows: list[Trade]` (the TradeTable), `dropped: int` | what `clean_trades` returns; callers take `.rows` | no |
| `CleanError` | `class CleanError(ValueError)` | the one error this section raises | no |

## Pipeline / workflow

`clean_trades(rows)` → `_dedupe` (first occurrence wins, keyed on all five fields) →
`sorted` by `(ts, symbol)` → `CleanResult`. Second step of the `daily` pipeline.

## Configuration

None.

## Running and testing

`uv run pytest packages/data/tests/unit/clean packages/data/tests/intent/clean`

## Implementation notes

- Returns `CleanResult` rather than a bare list so the `daily` pipeline can log `dropped`
  without recounting; callers take `.rows` for the table.
- Dedupe is by a field tuple: `Trade` is unhashable (ingest README, Implementation notes),
  so `set(rows)` is not an option.
- Dependencies consumed: `ingest` (`Trade`). Decisions applied: D1.
