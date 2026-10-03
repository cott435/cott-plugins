# Package contract — `data`

Written 2026-09-22 by `/dev-team:plan-package data`. Archived copy: `docs/history/2026-09-22-data-contract.md`.

## Purpose

Provides the **Trade** and **TradeTable** shapes of `docs/architecture.md`. Covers the
brief's `ingest` ("read the venue's CSV export as it comes, without the rows it repeats")
and `clean` ("one spelling per symbol; order by time") capabilities.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the CSV into Trade rows and drop the rows the export repeats (the **dedupe** step) | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `dataset:trades` |
| `clean` | write every symbol in its canonical form (the **normalise** step), sort by time | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

| section | name | signature | returns to |
|---|---|---|---|
| `ingest` | `load_trades` | `(path: Path, *, normalise: Callable[[str], str]) -> list[Trade]` — rows in file order with the repeats dropped. Two rows repeat each other when `ts`, `price`, `size`, `side` and `normalise(symbol)` are all equal; the first is kept, its symbol as read | `surface` |
| `ingest` | `Trade` | the **Trade** shape as a dataclass | everyone |
| `ingest` | `IngestError` | `class IngestError(ValueError)` | `surface` |
| `clean` | `normalise_symbol` | `(raw: str) -> str` — the canonical form of a symbol: stripped, upper-case | `surface`, which hands it to `load_trades` |
| `clean` | `clean_trades` | `(rows: list[Trade]) -> list[Trade]` — a TradeTable from rows whose repeats are already dropped: every symbol canonical, sorted by `ts` then `symbol` | `surface` |

## Pipelines

| pipeline | trigger | steps | crosses | failure | command |
|---|---|---|---|---|---|
| `daily` | the `data-daily` command | `ingest.load_trades(csv, normalise=clean.normalise_symbol)` — read, then dedupe → `clean.clean_trades` — normalise, then sort | `list[Trade]` at the arrow | any `<Section>Error` stops the run; the command exits 1 and writes nothing to stdout | `data-daily --csv <path>` |

## Public surface (intent)

| shape or name | realized by | consumer |
|---|---|---|
| **Trade** (`Trade`) | `ingest` | `analysis` |
| **TradeTable** (`daily`) | `surface` | `analysis` |
| `daily` pipeline | `surface` | `data-daily` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Standard library only (repo contract, Shared conventions). No `pandas`, no `attrs`.
- Every section logs one `INFO` line per step with `rows_in`, `rows_out`, `dropped`, whichever
  that step has.
- The dedupe step is `ingest`'s (Sections). `clean` and `surface` take rows whose repeats are
  already gone and never dedupe again.
- A canonical symbol has one definition, `clean.normalise_symbol`, and no other section
  restates its rule. `ingest` needs it for the dedupe key and may not import `clean` (repo
  contract, Dependency direction: `ingest` depends on nothing), so the pipeline hands the
  function to `load_trades` as `normalise`.

## Open decisions

- D1 — decided (UTC), scope `data/ingest`.
