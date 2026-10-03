# `data` — package contract

Written: 2026-09-26 by `/dev-team:plan-package data`, under `docs/architecture.md` (2026-09-26).
Package path: `packages/data`. Seeded for the `run-package` eval set (eval 16: the eval-5
package — two sections, `ingest` and `sessions`, that depend on nothing — planned under 2.6,
so the contract carries **Call paths** in the template's form and the `surface` section is
designed and tested right after PLAN, before either sibling is built).

## Purpose

Load the analyst's CSV export of trades, rejecting malformed rows by row and field, and list
the trading days a sequence of timestamps covers, with each day's first and last timestamp.
Covers the brief's `load trades`, and the trading-session helper `docs/architecture.md` adds.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | `load trades`: read `data/trades.csv` into `Trade` records in file order; reject a row with a missing or unparseable field and say which row and which field | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | `csv`, `datetime` (stdlib) | — | `dataset:trades` |
| `sessions` | trading sessions: the distinct UTC trading days in a sequence of tz-aware timestamps, and one day's first and last timestamp; works on `datetime` values only, never on `Trade` or the CSV | `packages/data/src/data/sessions/` | `docs/packages/data/design/sessions.md` | `datetime` (stdlib) | — | — |
| `surface` | §4 Pipelines and §6 Public surface: the package's top-level re-exports, the `data-days` command, `docs/packages/data/interface.md`. Its design is written right after PLAN, from this contract — **Section interfaces**, **Pipelines**, **Public surface (intent)** and **Call paths** — before any sibling is built, and its code is built last, from the shipped READMEs | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `sessions` | — |

## Section interfaces

Signatures are this package's; shapes are `docs/architecture.md` **Boundaries**. Every frame
**Call paths** names inside a section is an entry here.

### ingest

- `Trade` — the repo shape `Trade`, a frozen dataclass: `ts: datetime` (tz-aware UTC),
  `symbol: str`, `price: float`, `size: int`, `side: Literal["buy", "sell"]`.
- `read_trades(path: Path) -> list[Trade]` — every data row of the CSV, in file order,
  duplicates included. Opens the file itself: the `open` call is this function's, and it is
  the one file read the package makes (**Call paths**, `data-days`, frame 3).
- `IngestError(DataError)` — raised on the first rejected row, with `row: int` (1-based data
  row), `field: str` and `reason: str`; its message names all three.
- `DataError(Exception)` — the package base exception, defined here, re-raised nowhere else.

### sessions

- `trading_days(stamps: Iterable[datetime]) -> list[date]` — the distinct UTC dates of the
  stamps, ascending; an empty input gives `[]`. Raises `ValueError` naming the 0-based
  position of the first naive (tz-unaware) stamp. Pure: makes no external call.
- `session_bounds(stamps: Iterable[datetime], day: date) -> tuple[datetime, datetime]` — the
  earliest and the latest stamp whose UTC date is `day`, in any input order. Raises
  `ValueError` naming `day` when no stamp falls on it, and on a naive stamp as above. Pure.

`sessions` imports nothing from `ingest`: it takes timestamps, so it raises the standard
library's `ValueError` rather than `DataError`.

## Pipelines

- `list_trading_days(csv_path: Path) -> list[date]` — `ingest.read_trades` → the `ts` of each
  trade → `sessions.trading_days`. Returns the dates; writes nothing. Run by the `data-days`
  command, `data-days [--csv PATH]`: `[project.scripts]` entry `data-days = "data.cli:days"`,
  whose command function `cli.days` calls the pipeline and prints one ISO date per line on
  stdout, default path from configuration.

## Call paths

- `data-days` (budget 8):
  - file read: 1 `cli.days` → 2 `pipelines.list_trading_days` → 3 `ingest.read_trades` → `open`
  - stdout write: 1 `cli.days` → `print`

## Public surface (intent)

| name | kind | consumer |
|---|---|---|
| `data.Trade` | shape | the analyst |
| `data.read_trades` | function | the analyst |
| `data.trading_days` | function | the analyst |
| `data.session_bounds` | function | the analyst |
| `data.list_trading_days` | pipeline | the analyst, through `data-days` |
| `data.DataError` | exception | the analyst |

## Consumes

No upstream package. External: `dataset:trades` at `data/trades.csv`; probe
`docs/sources/trades.md`, which serves `data/ingest`. `sessions` reads no source: the probe's
**Shape** line (one session, 2026-09-01, `13:30:20Z` to `15:46:34Z`) is what its tests may
check against.

## Package conventions

- Configuration: `DATA_CSV` (default `data/trades.csv`), read in `configs.py` with
  `os.environ`.
- Logging: logger `data`.
- The intent suite lives at `tests/intent/<section>/` (the tester's); unit tests beside the
  package as `project-structure` places them.

## Open decisions

None.
