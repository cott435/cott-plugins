# ingest

## Purpose

`load trades`: reads the analyst's CSV export into `Trade` records, in file order, and rejects
a row with a missing or unparseable field by row and field. It parses and nothing more: a row
whose five fields parse is returned as read, whatever its values — duplicates, ordering and
whether a value is one a trade can have are `clean`'s.

## Files

- `__init__.py` — empty.
- `models.py` — the `Trade` shape.
- `errors.py` — `DataError`, `IngestError`.
- `reader.py` — `read_trades` and its per-field parsers.

## Entry points and interfaces

| name | signature | one-line use case | Public |
|---|---|---|---|
| `Trade` | `Trade(ts: datetime, symbol: str, price: float, size: int, side: Literal["buy", "sell"])` | one trade, a frozen dataclass; import from `data.ingest.models` | yes |
| `read_trades` | `read_trades(path: Path) -> list[Trade]` | every data row of the export, in file order, duplicates included; import from `data.ingest.reader` | no |
| `IngestError` | `IngestError(row: int, field: str, reason: str)` | raised on the first rejected row; `row` is the 1-based data row; import from `data.ingest.errors` | no |
| `DataError` | `DataError(Exception)` | the package base exception; import from `data.ingest.errors` | yes |

What `read_trades` guarantees of a returned `Trade`: `ts` is tz-aware UTC, parsed from the
`YYYY-MM-DDTHH:MM:SSZ` form; `symbol` is the non-empty string of the export, stripped of
surrounding whitespace and otherwise unchanged (case included); `price` is whatever `float()`
accepts, with no range check, so zero and negative prices pass; `size` is whatever `int()`
accepts, with no range check; `side` is `"buy"` or `"sell"`. Rows come back in file order,
which is not time order.

## Pipeline / workflow

- `read_trades` opens the file, reads it with `csv.DictReader`, and parses each row field by
  field; the first field that is absent, empty or unparseable raises `IngestError`.

## Configuration

- none; the path is the caller's. The package default is `DATA_CSV` (`data/trades.csv`), read
  by the package's `configs.py`, which the `surface` section builds.

## Running and testing

- `uv run pytest packages/data/tests/intent/ingest packages/data/tests/unit/ingest`
- `uv run python -c "from pathlib import Path; from data.ingest.reader import read_trades; print(len(read_trades(Path('data/trades.csv'))))"`

## Implementation notes

- No deviation from the design; no decision binds this section.
- `IngestError` stops at the first rejected row, as the contract says; it does not collect.
