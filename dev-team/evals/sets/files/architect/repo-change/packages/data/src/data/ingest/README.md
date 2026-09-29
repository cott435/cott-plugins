# `data/ingest`

## Purpose

Reads `data/trades.csv` into `Trade` records and stops on the first row with a missing or
unparseable field, naming the row and the field.

## Files

| File | What it holds |
|---|---|
| `model.py` | `Trade`, the repo contract's **Trades** record |
| `reader.py` | `read_export`, `_parse_row`, `_parse_ts` |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `Trade` | frozen dataclass `(ts, symbol, price, size, side)` | yes — contract §5, consumer `analysis/features` |
| `read_export` | `(path: Path) -> list[Trade]` | no |

## Pipeline / workflow

`csv.DictReader` → `_parse_row` per row → `list[Trade]` in file order. The first bad row
raises `TradeParseError(row, field, reason)`; nothing is returned.

## Configuration

none.

## Running and testing

`uv run pytest packages/data/tests/intent/ingest packages/data/tests/unit/ingest`

## Implementation notes

`side` accepts exactly `buy` and `sell` (contract §3). Row numbers count the header as row 1
(contract §7). No deviations recorded.
