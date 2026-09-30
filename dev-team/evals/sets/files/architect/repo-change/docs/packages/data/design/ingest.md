Mode: new

# Design — `data/ingest`

## Purpose and scope

Read `data/trades.csv` into `Trade` records; stop on the first bad row, naming it.

## Inputs and outputs

In: a CSV path. Out: `list[Trade]` in file order. Errors: `TradeParseError(row, field)`.

## Data model / internal contracts

`Trade` frozen dataclass per the repo contract's **Trades** shape.

### Module plan

| module | holds |
|---|---|
| `ingest/model.py` | `Trade` |
| `ingest/reader.py` | `read_export`, `_parse_row` |

## Workflow / pipeline

`csv.DictReader` → `_parse_row` per row → `list[Trade]`.

## Interfaces

| name | signature | public |
|---|---|---|
| `Trade` | dataclass | yes (contract §5) |
| `read_export` | `(path: Path) -> list[Trade]` | no |

## Error handling and logging

`TradeParseError` subclasses `DataError`; message `row <n>: <field> <reason>`. Rows are 1-based
counting the header as row 1. One `logging.info` per file read.

## Tests

`read_export` on the fixture returns 400 records; a missing field raises with the row number;
`side` other than `buy`/`sell` raises naming `side`; a naive `ts` raises naming `ts`.

## Pitfalls and risks

`fromisoformat` and a trailing `Z` on Python 3.10.

## Skills used

none.

## Contract deviations

none.

## Open questions

none.
