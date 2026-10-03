# Package contract — data

Written by `/dev-team:plan-package data` on 2026-09-19; edited on 2026-09-29 (the `window`
section added). Planned under `docs/architecture.md`. `ingest` shipped 2026-09-22, `clean`
2026-09-25 and `storage` 2026-09-26; `window` is next, and `surface` is the last row.

## Purpose

Own the bar data: parse CSV bar exports (`ingest`), drop the bars that cannot be trusted
(`clean`), persist and query what is left and keep the ledger of pipeline runs (`storage`),
hand `analysis` the bars of several symbols over one date window as a single frame
(`window`), and expose the package's pipeline, its command and its public names (`surface`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | parse CSV bar files into `Bar` records | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | — | — | — |
| clean | drop the bars that fail the price and volume checks, and duplicates | packages/data/src/data/clean | docs/packages/data/design/clean.md | — | ingest | — |
| storage | persist `Bar` records to the DuckDB file, query them by symbol and date range, and record each pipeline run in the `runs` table | packages/data/src/data/storage | docs/packages/data/design/storage.md | — | ingest | — |
| window | one entry point, `load_window`: fetch the bars of several symbols from the store or from CSV files, filter them to one date window, and merge them into a single `BarFrame` | packages/data/src/data/window | docs/packages/data/design/window.md | — | ingest, storage | — |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest, clean, storage, window | — |

## Section interfaces

### ingest (shipped — `packages/data/src/data/ingest/README.md` is the shipped document)

- `Bar` — the repo shape, a frozen dataclass; `ts` is tz-aware UTC.
- `load_bars(root: Path) -> list[Bar]` — parse every `*.csv` under `root`, files in path
  order, rows in file order. Raises `IngestError`: `data.ingest.no_files` when `root` holds
  no CSV file, `data.ingest.malformed_row` on a row that does not parse.

### clean (shipped — `packages/data/src/data/clean/README.md` is the shipped document)

- `clean_bars(bars: Sequence[Bar]) -> list[Bar]` — the bars that pass every check, in the
  order given: `low <= min(open, close)`, `max(open, close) <= high`, `volume >= 0`, and the
  first bar of each (`symbol`, `ts`). A dropped bar is logged at `warning`.
- Raises `CleanError` (`data.clean.nothing_left`) when the input was not empty and every bar
  was dropped.

### storage (shipped — `packages/data/src/data/storage/README.md` is the shipped document)

- `write_bars(bars: Sequence[Bar], *, run_id: str, db_path: Path | None = None) -> int` —
  upsert on (`symbol`, `ts`) into the DuckDB file at `db_path`, else `DATA_DB_PATH`. Returns
  the number of rows written and adds it to the `rows` of the `runs` row `run_id` names.
- `query_bars(symbol: str, start: date, end: date, *, db_path: Path | None = None) -> BarFrame`
  — inclusive range, sorted by `ts`; an empty frame when nothing matches.
- `recorded_run(pipeline: str, *, db_path: Path | None = None) -> RunRecorder` — records one
  run of the named pipeline as one row of the `runs` table (`run_id`, `pipeline`,
  `started_at`, `finished_at`, `status`, `rows`, `error_code`). The storage README says how a
  `RunRecorder` is used.
- Raises `StorageError`: `data.storage.unopenable`, `data.storage.write_failed`,
  `data.storage.unknown_run`.

### window

- `load_window(symbols: Sequence[str], start: date, end: date, *, kind: Literal["store", "csv"], root: Path | None = None, db_path: Path | None = None) -> BarFrame`
  — the section's one entry point. It runs three phases, in this order:
  1. **fetch** the candidate bars. Which fetch runs is chosen by `kind`: `store` reads each
     requested symbol's bars over the range from the DuckDB file, through `query_bars`
     (storage); `csv` parses every CSV file under `root`, through `load_bars` (ingest), and
     writes nothing to the store.
  2. **filter** them: keep the requested `symbols`; keep `start <= ts.date() <= end`, the
     date taken in UTC (a CSV file holds whatever symbols and dates the broker exported); and
     drop every bar whose `volume` is 0 (a halted day).
  3. **merge** what is left into one `BarFrame`: one row per (`symbol`, `ts`), the bar
     fetched last winning a duplicate, sorted by `symbol`, then `ts`. Nothing left is an
     empty frame, not an error.
- Raises `WindowError`: `data.window.bad_range` when `start > end`, before any fetch;
  `data.window.missing_root` when `kind` is `csv` and `root` is `None`;
  `data.window.unknown_kind` for a `kind` that is neither value. An `IngestError` or a
  `StorageError` raised by a fetch reaches the caller unchanged.
- `window` writes nothing: no bar to the store and no row to the `runs` ledger.

## Pipelines

- `ingest_csv(root: Path, *, db_path: Path | None = None) -> int` — three steps, in this
  order:
  1. `load_bars` (ingest) parses every CSV file under `root`;
  2. `clean_bars` (clean) drops the bars that fail its checks;
  3. `write_bars` (storage) upserts what is left.

  It returns the number of rows `write_bars` wrote. Every run is recorded in the run ledger,
  the `runs` table `storage` owns, through `recorded_run`: one row per run, opened before the
  first step and closed after the last as `ok`, or as `failed` with the error's `code` when a
  step raises. The error is then raised to the caller unchanged.
- The command `data-ingest ROOT [--db-path PATH]` calls `ingest_csv` and prints the number of
  rows written. A `DataError` is printed to stderr as `<code>: <message>` and the exit status
  is 1.

`load_window` is no pipeline: it serves none of the entries above and is called by `analysis`
directly.

## Public surface (intent)

| name | provided by | consumer |
|---|---|---|
| `Bar` | ingest | analysis |
| `query_bars` | storage | analysis |
| `load_window` | window | analysis |
| `ingest_csv` | surface (pipeline) | the command `data-ingest` |

## Consumes

Nothing from another package, and no external source.

## Package conventions

- Errors: one `DataError` subclass per section (`IngestError`, `CleanError`, `StorageError`,
  `WindowError`), defined in that section's `errors.py`. `DataError` itself, the repo shape,
  is in `packages/data/src/data/errors.py`, which the scaffold created.
- Imports: a section's `__init__.py` is empty, so inside the package a name is imported from
  the module that defines it. `data/__init__.py` alone re-exports, and only the public names.
- Config: each section's `configs.py`, prefix `DATA_`; storage owns `DATA_DB_PATH`, ingest
  owns `DATA_INGEST_DELIMITER` and `DATA_INGEST_TZ`. `window` has no setting of its own.
- Tests: `tests/intent/<section>/` (tester), `tests/unit/<section>/` (implementer).

## Open decisions

None open. D1 (DuckDB) is decided.
