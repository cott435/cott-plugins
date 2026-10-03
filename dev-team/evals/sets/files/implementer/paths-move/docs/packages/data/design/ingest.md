Mode: new

# Design — `data/ingest`

Written 2026-09-23 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Reads one trades CSV into **Trade** rows, in file order, with timestamps in UTC, and drops
the rows the export repeats (the contract's **dedupe** step). Owns the file and that one
step: no symbol rewriting and no sorting (that is `data/clean`), no persistence.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `path` | `Path` — one CSV with the columns `ts`, `symbol`, `price`, `size`, `side`, in any order | the `daily` pipeline |
| in | `normalise` | `Callable[[str], str]` — the canonical form of a symbol; the pipeline passes `clean.normalise_symbol` (contract, Package conventions) | the `daily` pipeline |
| out | the rows | `list[Trade]` in file order, repeats dropped, symbols as read | `data/clean`, through the `daily` pipeline |

Upstream packages: none

## 3. Data model / internal contracts

`Trade` — `@dataclass(slots=True)` with `ts: datetime`, `symbol: str`, `price: float`,
`size: int`, `side: str`, the **Trade** shape of the repo contract. No state, no
configuration (`configs.py` is not needed).

**Module plan** — under `packages/data/src/data/ingest/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `load_trades`, `Trade`, `IngestError` | — |
| `loader.py` | `Trade`, `IngestError`, `load_trades`, the CSV read, the per-cell parse and the dedupe | `load_trades`, `Trade`, `IngestError` |

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), first step: read, then dedupe.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `load_trades(path, normalise=…)` is called | open the file, UTF-8 | an open file | an `OSError` (missing file, a directory, no permission) becomes `IngestError`, `<file name>: cannot be read`, after one `WARNING` line `unreadable` |
| 2 | — | read the header row | the column names | `IngestError`, `<file name>: missing columns [...]`, when one of the five is absent |
| 3 | — | each record → `Trade`: `ts` parsed as ISO 8601 (`Z` accepted), a naive value taken as UTC (D1); `price` as `float`, `size` as `int`; `symbol` kept as read | `Trade` | `IngestError`, `<file name>:<line>: …`, for a cell that does not parse; `<line>` counts the header as line 1 |
| 4 | — | dedupe: walk the rows in file order with a `set` of keys seen, the key `(ts, normalise(symbol), price, size, side)`; the first row of each key is kept | the rows without repeats, in file order | none |
| 5 | — | log `rows_out` and `dropped`; return | `list[Trade]` | — |

The venue repeats a row with its symbol spelled another way (`aaa `, then `AAA`), which is
why the key takes the canonical symbol and not the cell. The kept row's own `symbol` is
left as read: rewriting it is `clean`'s normalise step.

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `load_trades` | `(path: Path, *, normalise: Callable[[str], str]) -> list[Trade]` | the `daily` pipeline | no | `IngestError` for an unreadable file, a missing column or a bad cell; a file with a header and no records returns `[]` |
| `Trade` | `@dataclass(slots=True)` — the **Trade** shape | everyone | yes | — |
| `IngestError` | `class IngestError(ValueError)` | `surface` | no | — |

## 6. Error handling and logging

Logger `data.ingest`. One `INFO` line `loaded` at step 5 with `path`, `rows_out` and
`dropped`; one `WARNING` line `unreadable` with `path` before the `IngestError` of step 1.
`extra=` keys only (repo contract, Shared conventions). Messages name the file and the line,
never a row's contents. `IngestError` is the one exception type this section raises. No
retries.

## 7. Tests

Unit (`packages/data/tests/unit/ingest/`): the timestamp parse on a naive value, a `Z` value
and an offset value; a missing file raises `IngestError` and logs `unreadable`; the dedupe
keeps the first of two rows whose symbols differ only in spelling.

Intent (`packages/data/tests/intent/ingest/`, the tester's): one file per §5 row.

Fixtures: small CSV files written to `tmp_path` in each suite's `conftest.py`.

## 8. Pitfalls and risks

1. `datetime.fromisoformat` rejects a trailing `Z` before Python 3.11 and the venue writes
   one; replace it with `+00:00` first.
2. `ingest` may not import `clean` (repo contract, Dependency direction), and the canonical
   symbol has one definition, which is `clean`'s (contract, Package conventions): the rule
   reaches the dedupe as the `normalise` argument and is never restated here.
3. `Trade` is unhashable; the dedupe keys on a tuple of fields, not on the row.

## 9. Skills used

- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.
- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration.

## 10. Contract deviations

None.

## 11. Open questions

- D1 binds this section: §4 step 3, a naive `ts` is taken as UTC.
