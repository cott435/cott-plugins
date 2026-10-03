# Repo contract

## Goal

A small trade store: load the vendor's daily trades file into one SQLite table and hand it
to the backfill package.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | `load-trades`, `store-trades`, `verify-trades` |
| `backfill` | `packages/backfill` | `data` | `reload-history` |

## Dependency graph

`backfill → data`. No cycles.

## Boundaries

- **trades table** — provided by `data`: the table `trades` of the SQLite database a run is
  given, with the columns `ts` (ISO 8601 text, UTC), `symbol` (text), `price` (real), `size`
  (integer). One row per line of the vendor's file.

## Shared conventions

- External sources: `file:vendor-trades` — a CSV with the header `ts,symbol,price,size`,
  probe doc `docs/sources/vendor-trades.md`.
- Logging is `loguru`. A log event's name starts with its package, `<pkg>.`.
- Timestamps are text in ISO 8601, UTC, everywhere inside the repo.

## Toolchain

```
uv run ruff check packages/<pkg>
uv run ruff format --check packages/<pkg>
uv run pytest packages/<pkg> -q
uv run lint-imports
```

## Non-goals

Intraday streaming; more than one vendor.

## Open decisions

- none
