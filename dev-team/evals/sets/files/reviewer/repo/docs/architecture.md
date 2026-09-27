# Repo contract

## Goal

A small market-data stack: pull daily bars from the vendor, clean them into one row per
symbol and business day, and hand them to the feature package.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | `daily-bars`, `clean-bars` |
| `features` | `packages/features` | `data` | `indicators` |

## Dependency graph

`features → data`. No cycles.

## Boundaries

- **BarFrame** — provided by `data`: a `pandas.DataFrame` with columns `symbol` (str),
  `timestamp` (naive UTC midnight), `open`, `high`, `low`, `close` (float64), `volume`
  (int64). One row per symbol and business day once cleaned.

## Shared conventions

- External sources: `api:vendor` — env var `VENDOR_KEY`, probe doc `docs/sources/vendor.md`.
- Every log event is named `<pkg>.<section>.<event>` and carries its fields in `extra`.
- Timestamps are naive and UTC everywhere inside the repo.
- No convention on retries beyond what each section's README states.

## Toolchain

```
uv run ruff check packages/<pkg>
uv run ruff format --check packages/<pkg>
uv run pytest packages/<pkg> -q
uv run lint-imports
```

## Non-goals

Intraday bars; corporate-action adjustment.

## Open decisions

- D2
