# data/ingest

Shipped 2026-09-22 (review `docs/reviews/2026-09-22-data-ingest-r1-s.md`, approved).

## Purpose

Parse CSV bar exports into `Bar` records. Owns the `Bar` dataclass. Does not persist anything.

## Files

- `models.py` — `Bar` (frozen dataclass).
- `loaders.py` — `discover_files`, `load_bars`, the CSV row parser.
- `errors.py` — `IngestError(DataError)`.
- `configs.py` — `IngestSettings` (prefix `DATA_`): `DATA_INGEST_DELIMITER` (default `,`).

## Entry points and interfaces

| name | signature | Public | consumed by |
|---|---|---|---|
| `Bar` | `@dataclass(frozen=True) Bar(symbol: str, ts: datetime, open: float, high: float, low: float, close: float, volume: int)` | yes (§5 `Bar` → analysis) | storage, prices, analysis |
| `load_bars` | `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` | no | `ingest_csv` pipeline |
| `discover_files` | `discover_files(root: Path) -> list[Path]` | no | `ingest_csv` pipeline |
| `IngestError` | `IngestError(DataError)`, codes `data.ingest.malformed_row`, `data.ingest.missing_column` | no | callers of `load_bars` |

`Bar.ts` is a **naive** `datetime` read verbatim from the CSV `timestamp` column (see
Implementation notes).

## Pipeline / workflow

`discover_files(root)` → for each file, stream rows → `Bar` per row → yield. A malformed row
raises `IngestError` and stops the iterator; nothing is skipped silently.

## Configuration

`DATA_INGEST_DELIMITER`, default `,`. Read once by `IngestSettings()` in `loaders.py`.

## Running and testing

`uv run pytest tests/intent/ingest tests/unit/ingest` — 14 intent, 9 unit, all green.

## Implementation notes

- `Bar.ts` is naive: the broker CSV carries `YYYY-MM-DD HH:MM:SS` with no offset and no zone
  column, and the contract row did not say which zone to assume. Not a `docs/deviations.md`
  entry: review r1 accepted it as matching the contract row as written. The tz-aware
  requirement in `docs/architecture.md` **Boundaries** is now the subject of
  `docs/changes/ingest-tz-aware-bars.md`.
- Rows are parsed with the `csv` module, not pandas, to keep the iterator lazy.
