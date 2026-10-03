# Repo contract — marketlab

Written by `/dev-team:plan-repo` on 2026-09-18. Shapes only; signatures live in the package
contracts.

## Goal

A small research workspace: `data` ingests, cleans and stores daily bars; `analysis` computes
signals over them.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | C1 ingest CSV bars, C2 clean them, C3 store bars and query them |
| analysis | packages/analysis | data | C4 momentum signals |

## Dependency graph

```
analysis → data
```

## Boundaries

Shapes that cross a package boundary. Shapes only — the package contract gives the signatures.

- `Bar` — `symbol: str`, `ts: datetime` (tz-aware UTC), `open`, `high`, `low`, `close: float`,
  `volume: int`. Provided by `data`; consumed by `analysis`.
- `BarFrame` — a pandas `DataFrame` with one row per `Bar`, indexed by (`symbol`, `ts`), the
  five price/volume columns as above.
- `DataError` — `code: str`, `message: str`, `context: dict[str, object]`. Every error a
  package raises across its boundary subclasses it.

## Shared conventions

- Errors: raise a `DataError` subclass; never a bare `Exception`; `code` is
  `<package>.<section>.<reason>`.
- Logging: `structlog`, keys `package` and `section` on every event, `run_id` on every event
  inside a recorded pipeline run, `symbol` when the event is about one symbol; level `info`
  for a step boundary, `warning` for a skipped record, `error` for a raised `DataError`.
- Time: every timestamp is tz-aware UTC at a package boundary.
- Config: pydantic-settings, env prefix `<PACKAGE>_` (`DATA_`, `ANALYSIS_`), one `configs.py`
  per section.
- Storage location: env var `DATA_DB_PATH`, default `./marketlab.duckdb` (D1).

## Toolchain

uv workspace, Python 3.12, ruff, pytest, import-linter (`analysis` may import `data`'s top
level only).

## Non-goals

Intraday bars; live or paper trading; anything but US equities; fetching bars from a vendor's
API.

## Open decisions

None open. D1 (store engine) is decided — see `docs/decisions.md`.
