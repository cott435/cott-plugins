# Package contract — data

Written by `/dev-team:plan-package data` on 2026-09-19; edited on 2026-09-27 (the `samples`
section added; the `prices` entry rewritten against the probe of 2026-09-24). Planned under
`docs/architecture.md`; `ingest` shipped 2026-09-22.

## Purpose

Own the bar data: parse CSV bar exports (`ingest`), fetch daily bars from Alpaca (`prices`),
persist and query them (`storage`), give other packages' tests sample bars (`samples`), and
expose the package's pipelines and public names (`surface`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | parse CSV bar files into `Bar` records | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | — | — | — |
| storage | persist `Bar` records to the DuckDB file and query them by symbol and date range | packages/data/src/data/storage | docs/packages/data/design/storage.md | — | ingest | — |
| prices | fetch daily bars from Alpaca and yield `Bar` records with adjusted closes | packages/data/src/data/prices | docs/packages/data/design/prices.md | — | ingest | api:alpaca |
| samples | give other packages' tests `Bar` records without a CSV file or the network: a pytest plugin, registered in the `pytest11` entry-point group under the name `marketlab_samples`, that provides the `make_bars` fixture | packages/data/src/data/samples | docs/packages/data/design/samples.md | — | ingest | — |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest, storage, prices | — |

## Section interfaces

### ingest (shipped — `packages/data/src/data/ingest/README.md` is the shipped document)

- `Bar` — the repo shape, a frozen dataclass.
- `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` — parse CSV files in order; raises
  `IngestError` (`data.ingest.malformed_row`) on a row that does not parse.
- `discover_files(root: Path) -> list[Path]` — every `*.csv` under `root`, sorted by path.

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
  per symbol-day from Alpaca's `GET /stocks/bars` with `timeframe=1Day`, following
  `next_page_token` until it is null. `ts` is the response's `t`, `volume` its `v`, and
  `close` its `c`, which Alpaca adjusts by the request's `adjustment` parameter; which value
  `fetch_bars` sends is D2 (open — until it is answered, the assumption in
  `docs/decisions.md`). A symbol with no bars in the range yields nothing.
- A `429` is retried after its `Retry-After` seconds and a `5xx` after a backoff, each at most
  `DATA_PRICES_MAX_RETRIES` times (default 3).
- Raises `PricesError`: `data.prices.bad_range` when `start > end`, before any request;
  `data.prices.unauthorized` on a `401`; `data.prices.bad_request` on a `422`;
  `data.prices.rate_limited` when a `429` outlasts the retries; `data.prices.unavailable` when
  a `5xx` outlasts the retries.

### samples

- `make_bars` — a pytest fixture, function scope. Its value is a callable
  `(symbol: str, days: int, *, start: date = date(2026, 1, 5)) -> list[Bar]`: `days` bars for
  `symbol`, one per weekday, the first on or after `start`, in date order. `ts` is 00:00 UTC
  of the bar's date, tz-aware. Every bar has `low <= min(open, close)`,
  `max(open, close) <= high` and `volume >= 0`. The same arguments always give equal bars.
- pytest finds the fixture through the plugin's `pytest11` entry point, named
  `marketlab_samples`: a consumer's test takes `make_bars` as an argument and imports nothing
  from `data.samples`. Because nothing imports it, `make_bars` is not a row of **Public
  surface (intent)**.
- Raises `SamplesError` (`data.samples.bad_request`) when `days < 1` or `symbol` is empty.

## Pipelines

- `ingest_csv(root: Path, db_path: Path | None = None) -> int` — `discover_files` →
  `load_bars` → `Store.write_bars`; steps served by ingest, ingest, storage; returns rows
  written.
- `refresh_prices(symbols: Sequence[str], start: date, end: date, db_path: Path | None =
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

- Errors: one `DataError` subclass per section (`IngestError`, `StorageError`, `PricesError`,
  `SamplesError`), defined in that section's `errors.py`.
- Config: each section's `configs.py`, prefix `DATA_`; storage owns `DATA_DB_PATH`, prices
  owns `DATA_PRICES_MAX_RETRIES`. The Alpaca keys keep the names `docs/architecture.md`
  **Shared conventions** gives them.
- Tests: `tests/intent/<section>/` (tester), `tests/unit/<section>/` (implementer).

## Open decisions

- D2 — which `adjustment` `fetch_bars` sends to Alpaca — is open; see `docs/decisions.md`.
- D1 (DuckDB) is decided.
