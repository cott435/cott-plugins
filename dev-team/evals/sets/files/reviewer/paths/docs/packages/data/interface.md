# Interface — `data`

The vendor's daily trades file loaded into the `trades` table of a SQLite database. Other
packages import the name below from `data.pipelines.load`, never from a section's module.

## Public names

| name | kind | signature | providing module | consumer | since |
|---|---|---|---|---|---|
| `run_load` | function | `(source: str, target: str) -> int` | `data.pipelines.load` | the `data-load` command; `backfill` | 2026-09-25 |

## Pipelines

- **load** — `data.pipelines.load.run_load`: `read_trades` (the CSV at `source`, oldest trade
  first) → `write_trades` (one row per trade in the `trades` table of the database at
  `target`). Returns the number of rows inserted. A file that is not CSV raises `csv.Error`
  after it is copied to `<source>.bad`; nothing is inserted.

## CLI commands

| command | entry point | arguments | what it runs |
|---|---|---|---|
| `data-load` | `data.cli:load` | `SOURCE TARGET` | the `load` pipeline; exits 0 when the run finished |

## Configuration

None.

## Shapes provided

- **trades table** — the table `trades` with the columns `ts` (text), `symbol` (text),
  `price` (real), `size` (integer), one row per trade.

## Deviations

None.

## Consumers (computed)

Snapshot, 2026-09-25: `backfill`.
