# Architecture — marketdata

Written 2026-09-22 by `/dev-team:plan-repo`. Archived copy: `docs/history/2026-09-22-architecture.md`.

## Goal

A daily pipeline that reads a trades CSV, removes exact duplicates, sorts by time, stores the
result in SQLite, and serves a tidy table to `analysis`.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | ingest, clean, store |
| `analysis` | `packages/analysis` | `data` | features, report |

## Dependency graph

`analysis` → `data`. No cycles.

## Boundaries

Shapes crossing package boundaries, by name:

- **Trade** — one trade: `ts` (timezone-aware UTC datetime), `symbol` (str), `price` (float),
  `size` (int), `side` (`"buy"` or `"sell"`). Provided by `data`.
- **TradeTable** — an ordered sequence of Trade, sorted by `ts` then `symbol`, no exact
  duplicates. Provided by `data`, consumed by `analysis`.

## Shared conventions

- Timezone: UTC everywhere; a naive timestamp read from a file is taken as UTC.
- Errors: each package raises subclasses of `ValueError` named `<Section>Error`; messages
  name the file and line where one applies, never the row's contents.
- Logging: `logging.getLogger("<pkg>.<section>")`, `INFO` per step with keys `rows_in`,
  `rows_out`, `dropped` where they apply; `extra=` only, never f-strings.
- External sources: `dataset:trades` at `data/trades.csv` (repo root), no credential.
- Dependencies: standard library only in `data`; `analysis` may use `pandas`.

## Toolchain

| item | value |
|---|---|
| language | Python 3.12 |
| package manager | `uv` workspace, `packages/*` |
| layout | `packages/<pkg>/src/<pkg>/<section>/` |
| tests | `pytest`; one package: `uv run pytest packages/<pkg>`; unit tests under `packages/<pkg>/tests/unit/<section>/`, intent tests under `packages/<pkg>/tests/intent/<section>/` |
| lint / format | `uv run ruff check`, `uv run ruff format --check` |
| types | `uv run mypy --strict packages/<pkg>/src` |
| imports | `uv run lint-imports` |
| docs | `uv run mkdocs build --strict` |

## Non-goals

Streaming input; more than one venue; anything but CSV in.

## Open decisions

- D1 — decided.
