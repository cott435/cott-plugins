# `data` — package contract

Status: contracted
Updated: 2026-09-20

## Purpose

Load, clean and store the analyst's trade export (`docs/brief.md`, area `data`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | read `data/trades.csv` into `Trade` rows; reject a row with a missing or unparseable field, naming the field | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | csv (stdlib) | — | dataset:trades |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest | — |

## Section interfaces

`ingest`: `load_trades(path: str | Path) -> list[Trade]`; raises `ValueError` naming the
field on a row with a missing or unparseable field.

## Pipelines

None yet.

## Public surface (intent)

| name | provided by | consumer |
|---|---|---|
| `load_trades` | ingest | analysis (planned) |

## Consumes

Nothing in-repo.

## Package conventions

UTC timestamps; standard library only.

## Open decisions

None.
