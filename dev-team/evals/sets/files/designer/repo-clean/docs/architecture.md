# Repo contract — marketlab

Written by `/dev-team:plan-repo` on 2026-09-18. Shapes only; signatures live in the package
contracts.

## Goal

A small research workspace: `data` ingests, fetches and stores daily bars; `analysis`
computes signals over them.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | C1 ingest CSV bars, C2 store and query bars, C3 fetch bars from Alpaca, C5 drop bad bars before they are stored |
| analysis | packages/analysis | data | C4 momentum signals |

## Dependency graph

```
analysis → data
```

## Boundaries

Shapes that cross a package boundary. Shapes only — the package contract gives the signatures.

- `Bar` — `symbol: str`, `ts: datetime` (UTC), `open`, `high`, `low`, `close: float`,
  `volume: int`. Provided by `data`; consumed by `analysis`.
- `BarFrame` — a pandas `DataFrame` with one row per `Bar`, indexed by (`symbol`, `ts`), the
  five price/volume columns as above.
- `DataError` — `code: str`, `message: str`, `context: dict[str, object]`. Every error a
  package raises across its boundary subclasses it.

## Shared conventions

- Errors: raise a `DataError` subclass; never a bare `Exception`; `code` is
  `<package>.<section>.<reason>`.
- Logging: `structlog`, keys `run_id`, `package`, `section`, `symbol` on every event; level
  `info` for a step boundary, `warning` for a skipped record, `error` for a raised `DataError`.
- Time: every timestamp is tz-aware UTC at a package boundary.
- Config: pydantic-settings, env prefix `<PACKAGE>_` (`DATA_`, `ANALYSIS_`), one `configs.py`
  per section.
- External sources: api `alpaca` — env vars `ALPACA_API_KEY`, `ALPACA_API_SECRET`; probe doc
  `docs/sources/alpaca.md`.
- Storage location: env var `DATA_DB_PATH`, default `./marketlab.duckdb` (D1).

## Toolchain

uv workspace, Python 3.12, ruff, pytest, import-linter (`analysis` may import `data`'s top
level only).

## Non-goals

Intraday bars; live or paper trading; anything but US equities.

## Open decisions

None open. D1 (store engine) is decided — see `docs/decisions.md`.
