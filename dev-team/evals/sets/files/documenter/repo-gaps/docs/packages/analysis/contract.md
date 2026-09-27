# Package contract — `analysis`

## Purpose

Derives the `features` shape from `data`'s clean `bars`.

## Sections

| Section | Responsibility | Path | Owner doc | Builds with | Depends on | Source |
|---|---|---|---|---|---|---|
| `features` | compute the feature columns for one run date | `packages/analysis/src/analysis/features` | `docs/packages/analysis/design/features.md` | — | — | — |
| `surface` | the package's pipelines (§4) and public surface (§5) | `packages/analysis/src/analysis` | `docs/packages/analysis/design/surface.md` | — | `features` | — |

## Section interfaces

`features` provides `build_features(bars: DataFrame) -> DataFrame`.

## Pipelines

`features_pipeline(run_date) -> Path`: read the landed bars, build features, write parquet.

## Public surface (intent)

| Name | Consumer |
|---|---|
| `build_features` | `report` |

## Consumes

| From | Names | Status |
|---|---|---|
| `docs/packages/data/interface.md` | `load_bars`, `clean_bars` | shipped |

## Package conventions

Env prefix `ANALYSIS_`.

## Open decisions

None.
