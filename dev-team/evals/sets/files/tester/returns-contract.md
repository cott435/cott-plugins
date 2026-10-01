# `features` — package contract

Written 2026-09-25 by /dev-team:plan-package features.

## Purpose

Computes per-symbol daily simple returns from `data`'s `BarTable`, and describes each run's
output as one manifest row so the `features-daily` command can list it beside `data`'s landed
files. Covers `returns` — section `returns`; brief Notes: "simple returns only, nothing
annualized".

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `returns` | computes daily simple returns per symbol from a `BarTable` and describes the result as one `LandingManifest` row | `packages/features/src/features/returns/` | `docs/packages/features/design/returns.md` | — | — | — |
| `surface` | the package's public surface: §4 Pipelines and §5 Public surface | `packages/features/src/features/` | `docs/packages/features/design/surface.md` | — | `returns` | — |

## Section interfaces

- `returns` → `FeatureError`, `daily_returns(bars) -> DataFrame` (a `ReturnTable`),
  `manifest_row(returns, run_date) -> dict[str, Any]`.

## Pipelines

- `features-daily` — trigger: the `features-daily` command with `--run-date`.
  `data.daily_pipeline` → `BarTable` → `returns.daily_returns` → `ReturnTable` → parquet under
  `FEATURES_DIR`; `returns.manifest_row` → one row appended to the run's manifest. Failure: a
  `FeatureError` aborts the run; nothing is written.

## Public surface (intent)

| name | realized by | consumer |
|---|---|---|
| `features_daily(run_date) -> Path` | `surface` | `features-daily` |

Nothing from `returns` is public.

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| `data` | `BarTable` | `docs/architecture.md` Boundaries; `docs/packages/data/interface.md` Shapes provided | shipped |
| `data` | `LandingManifest` | `docs/packages/data/interface.md` Shapes provided | shipped |

## Package conventions

- Returns are simple (`close / previous close - 1`), never log returns.

## Open decisions

None.
