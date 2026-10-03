Mode: new

# Design — `data/ingest`

Written 2026-09-23 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Reads one trades CSV into **Trade** rows, in file order, with timestamps in UTC. Owns the
file and nothing else: no dedupe and no sorting (that is `data/clean`), no persistence.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `path` | `Path` — one CSV with the columns `ts`, `symbol`, `price`, `size`, `side`, in any order | the `daily` pipeline |
| out | the rows | `list[Trade]` in file order | `data/clean`, the `daily` pipeline |

Upstream packages: none

## 3. Data model / internal contracts

`Trade` — `@dataclass(slots=True)` with `ts: datetime`, `symbol: str`, `price: float`,
`size: int`, `side: str`, the **Trade** shape of the repo contract. No state, no
configuration (`configs.py` is not needed).

**Module plan** — under `packages/data/src/data/ingest/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `load_trades`, `Trade`, `IngestError` | — |
| `loader.py` | `Trade`, `IngestError`, `load_trades`, the CSV read and the per-cell parse | `load_trades`, `Trade`, `IngestError` |

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), first step.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `load_trades(path)` is called | open the file, UTF-8 | an open file | an `OSError` (missing file, a directory, no permission) becomes `IngestError`, `<file name>: cannot be read`, after one `WARNING` line `unreadable` |
| 2 | — | read the header row | the column names | `IngestError`, `<file name>: missing columns [...]`, when one of the five is absent |
| 3 | — | each record → `Trade`: `ts` parsed as ISO 8601 (`Z` accepted), a naive value taken as UTC (D1); `price` as `float`, `size` as `int` | `Trade` | `IngestError`, `<file name>:<line>: …`, for a cell that does not parse; `<line>` counts the header as line 1 |
| 4 | — | log `rows_out`; return the rows in file order | `list[Trade]` | — |

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `load_trades` | `(path: Path) -> list[Trade]` | the `daily` pipeline | no | `IngestError` for an unreadable file, a missing column or a bad cell; a file with a header and no records returns `[]` |
| `Trade` | `@dataclass(slots=True)` — the **Trade** shape | everyone | yes | — |
| `IngestError` | `class IngestError(ValueError)` | `surface` | no | — |

## 6. Error handling and logging

Logger `data.ingest`. One `INFO` line `loaded` at step 4 with `path` and `rows_out`; one
`WARNING` line `unreadable` with `path` before the `IngestError` of step 1. `extra=` keys
only (repo contract, Shared conventions). Messages name the file and the line, never a
row's contents. `IngestError` is the one exception type this section raises. No retries.

## 7. Tests

Unit (`packages/data/tests/unit/ingest/`): the timestamp parse on a naive value, a `Z` value
and an offset value; a missing file raises `IngestError` and logs `unreadable`.

Intent (`packages/data/tests/intent/ingest/`, the tester's): one file per §5 row.

Fixtures: small CSV files written to `tmp_path` in each suite's `conftest.py`.

## 8. Pitfalls and risks

1. `datetime.fromisoformat` rejects a trailing `Z` before Python 3.11 and the venue writes
   one; replace it with `+00:00` first.
2. A naive timestamp is **taken as** UTC (`replace(tzinfo=…)`), an aware one is kept as it is.
3. `IngestError` is a `ValueError`: catching `ValueError` around the cell parse must not
   swallow an `IngestError` raised for the header.

## 9. Skills used

- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.
- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration.

## 10. Contract deviations

None.

## 11. Open questions

- D1 binds this section: §4 step 3, a naive `ts` is taken as UTC.
