# Package contract — data

Written by `/dev-team:plan-package data` on 2026-10-01. Planned under `docs/architecture.md`.
No section is built yet: `surface` is designed first, from this contract, and built last.
`storage` is ready to design beside it.

## Purpose

Own the bar data: parse CSV bar exports (`ingest`), drop the bars that cannot be trusted
(`clean`), persist and query what is left and keep the ledger of pipeline runs (`storage`),
and expose the package's pipelines, its commands and its public names (`surface`).

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | parse CSV bar files into `Bar` records | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | — | — | — |
| clean | drop the bars that fail the price and volume checks, and duplicates | packages/data/src/data/clean | docs/packages/data/design/clean.md | — | ingest | — |
| storage | persist `Bar` records to the DuckDB file, query them by symbol and date range, and record each pipeline run in the `runs` table | packages/data/src/data/storage | docs/packages/data/design/storage.md | — | ingest | — |
| surface | §4 Pipelines and §6 Public surface: `pipelines/`, `cli.py` and the top-level re-exports | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest, clean, storage | — |

## Section interfaces

### ingest

- `Bar` — the repo shape (`docs/architecture.md` **Boundaries**), a frozen dataclass; `ts` is
  tz-aware UTC, converted from the zone `DATA_INGEST_TZ` names.
- `load_bars(root: Path) -> list[Bar]` — parse every `*.csv` under `root`, files in path
  order, rows in file order; one `Bar` per row. Raises `IngestError`: `data.ingest.no_files`
  when `root` holds no CSV file, `data.ingest.malformed_row` on a row that does not parse, with
  the file and the line number in `context`.

### clean

- `clean_bars(bars: Sequence[Bar]) -> list[Bar]` — the bars that pass every check, in the
  order given: `low <= min(open, close)`, `max(open, close) <= high`, `volume >= 0`, and the
  first bar of each (`symbol`, `ts`). A dropped bar is logged at `warning` with the check's
  name and the bar's `symbol`. Changes no bar and stores nothing.
- Raises `CleanError` (`data.clean.nothing_left`) when the input was not empty and every bar
  was dropped.

### storage

- `write_bars(bars: Sequence[Bar], *, run_id: str, db_path: Path | None = None) -> int` —
  upsert on (`symbol`, `ts`) into the DuckDB file at `db_path`, else `DATA_DB_PATH`, in one
  transaction. Returns the number of rows written and adds it to the `rows` of the `runs` row
  `run_id` names.
- `query_bars(symbol: str, start: date, end: date, *, db_path: Path | None = None) -> BarFrame`
  — inclusive range, sorted by `ts`; an empty frame when nothing matches.
- `recorded_run(pipeline: str, *, db_path: Path | None = None) -> RunRecorder` — a context
  manager recording one run of the named pipeline as one row of the `runs` table (`run_id`,
  `pipeline`, `started_at`, `finished_at`, `status`, `rows`, `error_code`): the row is
  inserted with `status` `running` on entry and yields a `Run` (`id: str`, `pipeline: str`);
  a clean exit sets `finished_at` and `status` `ok`; a `DataError` raised inside the block sets
  `status` `failed` and `error_code` to the error's `code`, and the error propagates unchanged.
- Raises `StorageError`: `data.storage.unopenable`, `data.storage.write_failed`,
  `data.storage.unknown_run` (a `run_id` with no row in `runs`).

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
- `verify_csv(root: Path) -> int` — two steps, in this order:
  1. `load_bars` (ingest) parses every CSV file under `root`;
  2. `clean_bars` (clean) drops the bars that fail its checks.

  It returns the number of bars dropped (loaded minus kept). It writes nothing to the store
  and records no run: it is the dry run over a fresh export before `ingest_csv`.
- The command `data-ingest ROOT [--db-path PATH]` (`cli.ingest`) calls `ingest_csv` and prints
  the number of rows written. The command `data-verify ROOT` (`cli.verify`) calls `verify_csv`
  and prints the number of bars it would drop. A `DataError` is printed to stderr as
  `<code>: <message>` and the exit status is 1.

## Call paths

- `data-ingest` (budget 8):
  - file read: 1 `cli.ingest` → 2 `pipelines.ingest_csv` → 3 `ingest.load_bars` → `open`
  - database write: 1 `cli.ingest` → 2 `pipelines.ingest_csv` → 3 `storage.write_bars` → 4 `storage.open_store` → `duckdb.connect`
  - ledger write: 1 `cli.ingest` → 2 `pipelines.ingest_csv` → 3 `storage.recorded_run` → 4 `storage.open_store` → `duckdb.connect`
- `data-verify` (budget 8):
  - file read: 1 `cli.verify` → 2 `pipelines.verify_csv` → 3 `ingest.load_bars` → `open`

## Public surface (intent)

| name | provided by | consumer |
|---|---|---|
| `Bar` | ingest | analysis |
| `query_bars` | storage | analysis |
| `ingest_csv` | surface (pipeline) | the command `data-ingest` |
| `verify_csv` | surface (pipeline) | the command `data-verify` |

## Consumes

Nothing from another package, and no external source.

## Package conventions

- Errors: one `DataError` subclass per section (`IngestError`, `CleanError`, `StorageError`),
  defined in that section's `errors.py`. `DataError` itself, the repo shape, is in
  `packages/data/src/data/errors.py`, which the scaffold created.
- Imports: a section's `__init__.py` is empty, so inside the package a name is imported from
  the module that defines it. `data/__init__.py` alone re-exports, and only the public names.
- Config: each section's `configs.py`, prefix `DATA_`; storage owns `DATA_DB_PATH`, ingest
  owns `DATA_INGEST_DELIMITER` and `DATA_INGEST_TZ`.
- Tests: `tests/intent/<section>/` (tester), `tests/unit/<section>/` (implementer).

## Open decisions

None open. D1 (DuckDB) is decided.
