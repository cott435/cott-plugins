# data/storage

Shipped 2026-09-26 (review round 2, approved).

## Purpose

Persist `Bar` records to one DuckDB file and query them by symbol and date range. Owns the
`bars` table and the `runs` table, the ledger of pipeline runs. Parses nothing and cleans
nothing.

## Files

- `store.py` — `write_bars`, `query_bars`, the `bars` table.
- `ledger.py` — `recorded_run`, `RunRecorder`, `Run`, the `runs` table.
- `errors.py` — `StorageError(DataError)`.
- `configs.py` — `StorageSettings` (prefix `DATA_`): `DATA_DB_PATH` (default
  `./marketlab.duckdb`, D1).
- `__init__.py` — empty.

## Entry points and interfaces

| name | signature | Public | consumed by |
|---|---|---|---|
| `write_bars` | `write_bars(bars: Sequence[Bar], *, run_id: str, db_path: Path \| None = None) -> int` | no | `ingest_csv` pipeline |
| `query_bars` | `query_bars(symbol: str, start: date, end: date, *, db_path: Path \| None = None) -> BarFrame` | yes (§5 `query_bars` → analysis) | analysis |
| `recorded_run` | `recorded_run(pipeline: str, *, db_path: Path \| None = None) -> RunRecorder` | no | `ingest_csv` pipeline |
| `RunRecorder` | a context manager yielding a `Run`; also `RunRecorder.call(step: Callable[[Run], T]) -> T` | no | `ingest_csv` pipeline |
| `Run` | `@dataclass(frozen=True) Run(id: str, pipeline: str)` | no | `ingest_csv` pipeline |
| `StorageError` | `StorageError(DataError)`, codes `data.storage.unopenable`, `data.storage.write_failed`, `data.storage.unknown_run` | no | callers of the four above |

`Bar` is `ingest`'s (`packages/data/src/data/ingest/README.md`). `BarFrame` is the repo shape
in `docs/architecture.md` **Boundaries**. Wherever `db_path` is `None` the file is the one
`DATA_DB_PATH` names.

## The run ledger

`recorded_run(pipeline)` returns a `RunRecorder` for one run of the named pipeline. It is
used in one of two ways, and either records the same row in `runs`:

- **As a context manager.** `with recorded_run("ingest_csv", db_path=db_path) as run:`
  inserts the row with `status` `running` on entry and yields the `Run`. On a clean exit it
  sets `finished_at` and `status` `ok`. When the block raises a `DataError` it sets `status`
  `failed` and `error_code` to the error's `code`, and the error propagates unchanged; any
  other exception is recorded as `failed` with `error_code` `unexpected` and propagates too.
- **Through `RunRecorder.call`.** `recorded_run("ingest_csv", db_path=db_path).call(step)`
  opens the run the same way, calls `step(run)`, closes the run the same way, and returns
  what `step` returned. `step` is any `Callable[[Run], T]`.

`write_bars(…, run_id=run.id)` adds the count it wrote to that run's `rows`; a `run_id` with
no row in `runs` raises `StorageError` (`data.storage.unknown_run`).

## Pipeline / workflow

`write_bars`: open the file → create `bars` when absent → upsert on (`symbol`, `ts`) in one
transaction → add the count to the run's `rows` → return the count. `query_bars`: open the
file read-only → select the symbol's rows with `start <= ts.date() <= end` → a `BarFrame`
sorted by `ts`, empty when nothing matches. A file that cannot be opened raises
`StorageError` (`data.storage.unopenable`); a failed transaction is rolled back and raises
`StorageError` (`data.storage.write_failed`).

## Configuration

`DATA_DB_PATH`, default `./marketlab.duckdb`. Read once by `StorageSettings()` in `store.py`
and in `ledger.py`.

## Running and testing

`uv run pytest tests/intent/storage tests/unit/storage` — 17 intent, 12 unit, all green.

## Implementation notes

- `run_id` is a UUID4 string made when the run is opened.
- The `runs` row and the `bars` upsert are separate transactions: a failed upsert leaves the
  run row in place, closed as `failed`.
