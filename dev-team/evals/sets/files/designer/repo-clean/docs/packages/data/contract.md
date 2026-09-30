# Package contract — data

Written by `/dev-team:plan-package data` on 2026-09-19. Planned under
`docs/architecture.md`; `ingest` shipped 2026-09-22.

## Purpose

Own the bar data: parse CSV bar exports (`ingest`), fetch daily bars from Alpaca (`prices`),
drop bad bars (`clean`), persist and query them (`storage`), and expose the package's
pipelines and public names (`surface`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | parse CSV bar files into `Bar` records | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | — | — | — |
| clean | drop `Bar` records that fail the OHLC, volume or duplicate checks before they are stored | packages/data/src/data/clean | docs/packages/data/design/clean.md | — | ingest | — |
| storage | persist `Bar` records to the DuckDB file and query them by symbol and date range | packages/data/src/data/storage | docs/packages/data/design/storage.md | — | ingest | — |
| prices | fetch daily bars from Alpaca and yield `Bar` records with adjusted closes | packages/data/src/data/prices | docs/packages/data/design/prices.md | — | ingest | api:alpaca |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest, clean, storage, prices | — |

## Section interfaces

### ingest (shipped — `packages/data/src/data/ingest/README.md` is the shipped document)

- `Bar` — the repo shape, a frozen dataclass.
- `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` — parse CSV files in order; raises
  `IngestError` (`data.ingest.malformed_row`) on a row that does not parse.
- `discover_files(root: Path) -> list[Path]` — every `*.csv` under `root`, sorted by path.

### clean

- `clean_bars(bars: Iterable[Bar]) -> Iterator[Bar]` — lazily yield each bar that passes
  every check, in input order, and drop the rest. The checks, each with its reason name:
  `ohlc` — `low <= min(open, close)` and `max(open, close) <= high`; `volume` —
  `volume >= 0`; `duplicate` — a (`symbol`, `ts`) already yielded. One `warning` event per
  dropped bar, with the reason under the key `reason`.
- Raises nothing: a bar that fails a check is dropped, never raised.

### storage

- `open_store(path: Path | None = None) -> Store` — open the DuckDB file at `path`, else
  `DATA_DB_PATH`; create the `bars` table when absent.
- `Store.write_bars(bars: Iterable[Bar]) -> int` — upsert on (`symbol`, `ts`); returns the
  number of rows written.
- `Store.query_bars(symbol: str, start: date, end: date) -> BarFrame` — inclusive range,
  sorted by `ts`; empty frame when nothing matches.
- Raises `StorageError` (`data.storage.<reason>`) for an unopenable file or a failed write.

### prices

- `fetch_bars(symbols: Sequence[str], start: date, end: date) -> Iterator[Bar]` — one `Bar`
  per symbol-day from the Alpaca daily bars endpoint. Each bar's `close` is the response's
  `adjusted_close` field, so a consumer never sees an unadjusted close; `volume` is the
  response's `volume` field.
- Raises `PricesError` (`data.prices.<reason>`) on a non-2xx response after retries.

## Pipelines

- `ingest_csv(root: Path, db_path: Path | None = None) -> int` — `discover_files` →
  `load_bars` → `clean_bars` → `Store.write_bars`; steps served by ingest, ingest, clean,
  storage; returns rows written.
- `check_csv(root: Path) -> dict[str, int]` — a dry run: `discover_files` → `load_bars` →
  the number of bars clean would drop, per reason (`ohlc`, `volume`, `duplicate`; a reason
  with no drops maps to 0); steps served by ingest, ingest, clean. Nothing is written.
- `refresh_prices(symbols: Sequence[str], start: date, end: date, db_path: Path | None =
  None) -> int` — `fetch_bars` → `clean_bars` → `Store.write_bars`; served by prices, clean,
  storage.

## Public surface (intent)

| name | provided by | consumer |
|---|---|---|
| `Bar` | ingest | analysis |
| `query_bars` | storage | analysis |
| `ingest_csv` | surface (pipeline) | CLI `marketlab ingest` |
| `refresh_prices` | surface (pipeline) | CLI `marketlab refresh` |
| `check_csv` | surface (pipeline) | CLI `marketlab check` |

## Consumes

Nothing from another package. External: `api:alpaca` — see `docs/sources/alpaca.md`.

## Package conventions

- Errors: one `DataError` subclass per section that raises (`IngestError`, `StorageError`,
  `PricesError`), defined in that section's `errors.py`; `clean` raises nothing.
- Config: each section's `configs.py`, prefix `DATA_`; storage owns `DATA_DB_PATH`.
- Tests: `tests/intent/<section>/` (tester), `tests/unit/<section>/` (implementer).

## Open decisions

None open. D1 (DuckDB) is decided.
