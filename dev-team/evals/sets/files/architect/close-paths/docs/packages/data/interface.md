# Interface — `data`

The vendor's daily trades file loaded into the `trades` table of a SQLite database, and the
vendor's drop directory checked before a load. Other packages import the names below from
`data.pipelines.load` and `data.pipelines.verify`, never from a section's module.

## Public names

| name | kind | signature | providing module | consumer | since |
|---|---|---|---|---|---|
| `run_load` | function | `(source: str, target: str) -> int` | `data.pipelines.load` | the `data-load` command; `backfill` | 2026-09-25 |
| `run_verify` | function | `(source_dir: str) -> list[str]` | `data.pipelines.verify` | the `data-verify` command | 2026-09-27 |

## Pipelines

- **load** — `data.pipelines.load.run_load`: `read_trades` (the CSV at `source`, oldest trade
  first) → `write_trades` (one row per trade in the `trades` table of the database at
  `target`). Returns the number of rows inserted. A file that is not CSV raises `csv.Error`
  after it is copied to `<source>.bad`; nothing is inserted.
- **verify** — `data.pipelines.verify.run_verify`: for every file under `source_dir`, in name
  order, `check_header` (the file's first row against `ts,symbol,price,size`), re-read up to
  twice when the file is not yet CSV. Returns the paths that failed; writes nothing.

## CLI commands

| command | entry point | arguments | what it runs |
|---|---|---|---|
| `data-load` | `data.cli:load` | `SOURCE TARGET` | the `load` pipeline; exits 0 when the run finished |
| `data-verify` | `data.cli:verify` | `SOURCE_DIR` | the `verify` pipeline; exits 1 when any file failed, else 0 |

## Configuration

None.

## Shapes provided

- **trades table** — the table `trades` with the columns `ts` (text), `symbol` (text),
  `price` (real), `size` (integer), one row per trade.

## Deviations

None.

## Consumers (computed)

Snapshot, 2026-09-27: `backfill`.
