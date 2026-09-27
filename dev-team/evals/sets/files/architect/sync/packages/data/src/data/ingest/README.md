# `data/ingest`

## Purpose

Reads `data/trades.csv` into `Trade` records and stops on the first row with a missing or
unparseable field, naming the row and the field.

## Files

| File | What it holds |
|---|---|
| `model.py` | `Trade`, the repo contract's **Trades** record |
| `reader.py` | `read_export`, `_parse_row`, `_parse_ts`, `SIDE_ALIASES` |

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

`side` accepts `buy`, `sell` and the aliases `B` and `S` (case-insensitive), normalized to
`buy`/`sell` before the record is built — `docs/changes/side-aliases.md`; the stored **Trades**
shape is unchanged. Row numbers count the header as row 1
(contract §7). A proposed skip of bad rows was rejected (`docs/deviations.md`, `data/ingest — 2026-09-23`):
the run still stops on the first bad row.
