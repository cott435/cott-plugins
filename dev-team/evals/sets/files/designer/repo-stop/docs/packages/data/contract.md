# Package contract — data

Written by `/dev-team:plan-package data` on 2026-09-19. Planned under
`docs/architecture.md`; `ingest` shipped 2026-09-22.

## Purpose

Own the bar data: parse CSV bar exports (`ingest`), fetch daily bars from Alpaca (`prices`),
persist and query them (`storage`), and expose the package's pipelines and public names
(`surface`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | parse CSV bar files into `Bar` records | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | — | — | — |
| storage | persist `Bar` records to the bar store and query them by symbol and date range | packages/data/src/data/storage | docs/packages/data/design/storage.md | — | ingest | — |
| prices | fetch daily bars from Alpaca and yield `Bar` records with adjusted closes | packages/data/src/data/prices | docs/packages/data/design/prices.md | — | ingest | api:alpaca |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest, storage, prices | — |

## Section interfaces

### ingest (shipped — `packages/data/src/data/ingest/README.md` is the shipped document)

- `Bar` — the repo shape, a frozen dataclass.
- `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` — parse CSV files in order; raises
  `IngestError` (`data.ingest.malformed_row`) on a row that does not parse.
- `discover_files(root: Path) -> list[Path]` — every `*.csv` under `root`, sorted by path.

### storage

- `open_store(url: str | None = None) -> Store` — open the bar store at `url`, else
  `DATA_STORE_URL`; create the `bars` table when absent. What `url` is — a file path or a
  server DSN — follows the engine (**Open decisions**).
- `Store.write_bars(bars: Iterable[Bar]) -> int` — upsert on (`symbol`, `ts`); returns the
  number of rows written.
- `Store.query_bars(symbol: str, start: date, end: date) -> BarFrame` — inclusive range,
  sorted by `ts`; empty frame when nothing matches.
- Raises `StorageError` (`data.storage.<reason>`) for a store it cannot open or a failed
  write.

### prices

- `fetch_bars(symbols: Sequence[str], start: date, end: date) -> Iterator[Bar]` — one `Bar`
  per symbol-day from the Alpaca daily bars endpoint. Each bar's `close` is the response's
  `adjusted_close` field, so a consumer never sees an unadjusted close; `volume` is the
  response's `volume` field.
- Raises `PricesError` (`data.prices.<reason>`) on a non-2xx response after retries.

## Pipelines

- `ingest_csv(root: Path, store_url: str | None = None) -> int` — `discover_files` →
  `load_bars` → `Store.write_bars`; steps served by ingest, ingest, storage; returns rows
  written.
- `refresh_prices(symbols: Sequence[str], start: date, end: date, store_url: str | None =
  None) -> int` — `fetch_bars` → `Store.write_bars`; served by prices, storage.

## Public surface (intent)

| name | provided by | consumer |
|---|---|---|
| `Bar` | ingest | analysis |
| `query_bars` | storage | analysis |
| `ingest_csv` | surface (pipeline) | CLI `marketlab ingest` |
| `refresh_prices` | surface (pipeline) | CLI `marketlab refresh` |

## Consumes

Nothing from another package. External: `api:alpaca` — see `docs/sources/alpaca.md`.

## Package conventions

- Errors: one `DataError` subclass per section (`IngestError`, `StorageError`,
  `PricesError`), defined in that section's `errors.py`.
- Config: each section's `configs.py`, prefix `DATA_`; storage owns `DATA_STORE_URL`.
- Tests: `tests/intent/<section>/` (tester), `tests/unit/<section>/` (implementer).

## Open decisions

- **The bar store's engine** — an embedded file database or a database server — is not
  chosen, and the user has named no default. It fixes what `open_store`'s `url` is, the
  upsert statement behind `write_bars`, the driver dependency `storage` adds, and whether
  `ingest_csv` and `refresh_prices` may write at the same time. `storage` cannot be designed
  until it is chosen; no design assumes one. Not yet raised in `docs/decisions.md`.
