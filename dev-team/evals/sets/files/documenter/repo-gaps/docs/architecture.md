# Architecture — marketdata

## Goal

A daily pipeline that pulls vendor bars, cleans them, derives features from the clean table,
and, later, renders a report.

## Packages

| Package | Path | Depends on | Covers |
|---|---|---|---|
| `data` | `packages/data` | — | ingest, clean |
| `analysis` | `packages/analysis` | `data` | features |
| `report` | `packages/report` | `analysis` | daily report |

## Dependency graph

`data` ← `analysis` ← `report`.

## Boundaries

`bars`: one row per symbol per session, columns `ts, symbol, open, high, low, close, volume`.
`features`: `bars` plus one column per feature, keyed the same way.

## Shared conventions

External sources: the vendor API is `api:vendor`, credential `DATA_VENDOR_KEY`. Every package
reads its settings from environment variables with its own prefix (`DATA_`, `ANALYSIS_`).

## Toolchain

```
uv run ruff check .
uv run pytest
```

## Non-goals

Intraday bars. A web front end.

## Open decisions

D2.
