# Architecture — marketdata

Goal: pull daily vendor bars for a symbol list, clean them, and serve one tidy table to the
`features` package. Contracted 2026-09-20 against `docs/brief.md`.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | `daily-bars` |
| `features` | `packages/features` | `data` | `returns` |

## Dependency graph

`features` → `data`. No cycles.

## Boundaries

- `BarTable` — a DataFrame with columns `symbol: str`, `ts: datetime (tz-aware UTC)`,
  `open`, `high`, `low`, `close: float`, `volume: int`; one row per symbol per session,
  sorted by `symbol, ts`. Provided by `data`, consumed by `features`.

## Shared conventions

- **Errors**: every package error subclasses `Exception`, carries `.reason: str`, and its
  `str()` is `f"{reason}: {detail}"`. Callers match on `.reason`, never on the message.
- **Logging**: stdlib `logging`, one logger per section named `<pkg>.<section>`. A record's
  message is `key=value` pairs starting with `event=<pkg>.<section>.<verb>`.
- **Timestamps**: tz-aware UTC everywhere (D1). Naive datetimes never cross a section boundary.
- **External sources**: `api:polygon` — key in env var `DATA_VENDOR_KEY`, base URL
  `https://api.polygon.io`, probed in `docs/sources/polygon.md`.

## Toolchain

This fixture is a plain checkout, not a uv workspace: `python` and `ruff` are on PATH and
every command runs from the package root (`packages/<pkg>`) with `src` on `PYTHONPATH`.

| purpose | command |
|---|---|
| package tests | `PYTHONPATH=src python -m pytest tests -q` |
| one-package intent tests | `PYTHONPATH=src python -m pytest tests/intent/<section> -q` |
| formatter | `ruff format <path>` |
| linter | `ruff check --fix <path>` |
| import direction | `lint-imports` (contracts in `importlinter.toml`) |

## Non-goals

Intraday bars; more than one vendor.

## Open decisions

- D2 — zero-volume bars: keep or drop (scope `data/ingest`).
