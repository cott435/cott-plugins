# Package contract — `data`

## Purpose

Ingests vendor bars and cleans them into the repo's `bars` shape.

## Sections

| Section | Responsibility | Path | Owner doc | Builds with | Depends on | Source |
|---|---|---|---|---|---|---|
| `ingest` | pull daily bars from the vendor and land them | `packages/data/src/data/ingest` | `docs/packages/data/design/ingest.md` | `vendor-client` | — | `api:vendor` |
| `clean` | apply the cleaning rules to landed bars | `packages/data/src/data/clean` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | the package's pipelines (§4) and public surface (§5) | `packages/data/src/data` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

`ingest` provides `load_bars(symbol, start, end) -> DataFrame`; `clean` provides
`clean_bars(df) -> DataFrame`.

## Pipelines

`daily_pipeline(run_date) -> Path`: ingest, clean, write parquet.

## Public surface (intent)

| Name | Consumer |
|---|---|
| `load_bars` | `analysis` |
| `clean_bars` | `analysis` |
| `data-daily` (command) | the user |

## Consumes

| From | Names | Status |
|---|---|---|
| `docs/sources/vendor.md` | `/v1/bars` | observed |

## Package conventions

Env prefix `DATA_`.

## Open decisions

D2.
