# data/ingest

Shipped 2026-09-22 (review round 1, approved).

## Purpose

Parse CSV bar exports into `Bar` records. Owns the `Bar` dataclass. Does not persist anything.

## Files

- `models.py` — `Bar` (frozen dataclass).
- `loaders.py` — `load_bars`, the CSV row parser.
- `errors.py` — `IngestError(DataError)`.
- `configs.py` — `IngestSettings` (prefix `DATA_`): `DATA_INGEST_DELIMITER` (default `,`),
  `DATA_INGEST_TZ` (default `America/New_York`).
- `__init__.py` — empty.

## Entry points and interfaces

| name | signature | Public | consumed by |
|---|---|---|---|
| `Bar` | `@dataclass(frozen=True) Bar(symbol: str, ts: datetime, open: float, high: float, low: float, close: float, volume: int)` | yes (§5 `Bar` → analysis) | clean, storage, analysis |
| `load_bars` | `load_bars(root: Path) -> list[Bar]` | no | `ingest_csv` pipeline |
| `IngestError` | `IngestError(DataError)`, codes `data.ingest.no_files`, `data.ingest.malformed_row` | no | callers of `load_bars` |

`Bar.ts` is tz-aware UTC: the CSV `timestamp` column is read in the zone `DATA_INGEST_TZ`
names and converted.

## Pipeline / workflow

Find every `*.csv` under `root`, sorted by path → for each file, parse its rows in order →
one `Bar` per row → return the list. A directory with no CSV file raises `IngestError`
(`data.ingest.no_files`). A malformed row raises `IngestError` (`data.ingest.malformed_row`)
with the file and the line number in `context`; nothing is skipped silently.

## Configuration

`DATA_INGEST_DELIMITER`, default `,`, and `DATA_INGEST_TZ`, default `America/New_York`. Read
once by `IngestSettings()` in `loaders.py`.

## Running and testing

`uv run pytest tests/intent/ingest tests/unit/ingest` — 14 intent, 9 unit, all green.

## Implementation notes

- Rows are parsed with the `csv` module, not pandas.
- The whole list is built before it is returned: an export is a few thousand rows.
