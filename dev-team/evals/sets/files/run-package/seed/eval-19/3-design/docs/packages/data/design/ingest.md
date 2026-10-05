# data/ingest — design
Mode: new

Written 2026-09-27 from `docs/packages/data/contract.md` (the `ingest` row and **Section
interfaces**, `ingest`), `docs/architecture.md` (**Boundaries**, `Trade`; **Shared
conventions**) and the probe `docs/sources/trades.md`. Seeded for the `run-package` eval set
(eval 19), in the shape the designer writes.

## 1. Purpose and scope

Owns `load trades`: reading `data/trades.csv` into `Trade` records in file order, and rejecting
a row with a missing or unparseable field by row and field. Does not own duplicates, ordering
or whether a parsed value is a plausible one: those are `clean`'s (`docs/sources/trades.md`,
**Sections served**).

## 2. Inputs and outputs

- In: a path to the CSV export — one header line `ts,symbol,price,size,side`, then one trade
  per line, comma-separated, unquoted, UTF-8 (`docs/sources/trades.md`, **Access**).
- Out: `list[Trade]`, the repo shape (`docs/architecture.md`, **Boundaries**): `ts` tz-aware
  UTC, `symbol` str, `price` float, `size` int, `side` `"buy"` or `"sell"`.

## 3. Data model / internal contracts

`Trade` is a frozen dataclass in `models.py`. No state, no table.

## 4. Workflow / pipeline

1. Open the file as UTF-8 and read it with `csv.DictReader`. Failure: the file is missing —
   the `OSError` propagates unchanged.
2. For each data row, numbered from 1 in file order, parse the five fields in column order:
   `ts` from the `YYYY-MM-DDTHH:MM:SSZ` form to a tz-aware UTC datetime; `symbol` as the
   non-empty string, stripped; `price` with `float`; `size` with `int`; `side` as one of `buy`
   and `sell`. Failure: the first field that is absent, empty or unparseable raises
   `IngestError` and the read stops.
3. Return the trades in file order, duplicates included.

## 5. Interfaces

| name | signature | errors | Public |
|---|---|---|---|
| `Trade` | frozen dataclass, the five fields of §2 | — | yes |
| `read_trades` | `read_trades(path: Path) -> list[Trade]` | `IngestError` on the first rejected row | no |
| `IngestError` | `IngestError(row: int, field: str, reason: str)`, a `DataError` | — | no |
| `DataError` | `DataError(Exception)` | — | yes |

## 6. Error handling and logging

`IngestError` carries `row` (1-based data row), `field` and `reason`, and its message names all
three (`docs/architecture.md`, **Shared conventions**, Errors). Nothing is logged: the caller
decides what a rejected export means.

## 7. Tests

1. Three rows, the second out of time order and the third an exact duplicate of the second →
   three trades, in file order.
2. One row → its `ts` is tz-aware with a zero UTC offset.
3. A second row whose `price` is `eight` → `IngestError` with `row == 2`, `field == "price"`,
   and a message naming the row, the field and the reason.
4. A row whose `size` is empty → `IngestError`, which is a `DataError`, with `field == "size"`.

The export itself has no rejected row (`docs/sources/trades.md`, **Quirks**), so every case
builds its own file.

## 8. Pitfalls and risks

- A repo-root `data/` directory shares the package's name; imports resolve through the
  workspace environment, never through the working directory.
- A value that parses is returned whatever it is: `float` accepts `-1.5` and `int` accepts `0`.
  That is the contract's line between `ingest` and `clean`, not an omission.

## 9. Skills used

- `python-style-guide` — docstrings, annotations, exception chaining.
- `project-structure` — one module per concern, an empty nested `__init__.py`.

## 10. Contract deviations

None.

## 11. Open questions

None.
