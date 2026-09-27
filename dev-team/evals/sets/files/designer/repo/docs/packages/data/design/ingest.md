# Design — data/ingest

Designed 2026-09-20 by `dev-team:designer` (mode `new`). Shipped 2026-09-22.

## 1. Purpose and scope

Parse CSV bar exports into `Bar` records. Owns `Bar`. Does not persist, fetch or
deduplicate.

## 2. Inputs and outputs

- In: `root: Path` (a directory of `*.csv` exports) or explicit `paths`. Columns per
  `docs/packages/data/contract.md` **Section interfaces** › ingest: `symbol`, `timestamp`,
  `open`, `high`, `low`, `close`, `volume`.
- Out: `Iterator[Bar]`, `Bar` being the repo shape in `docs/architecture.md` **Boundaries**.

## 3. Data model / internal contracts

`Bar` — frozen dataclass of the repo shape. No other state.

**Module plan** (`packages/data/src/data/ingest/`):

- `models.py` — `Bar` (§5).
- `loaders.py` — `discover_files`, `load_bars`, `_parse_row` (§5).
- `errors.py` — `IngestError`.
- `configs.py` — `IngestSettings`: `DATA_INGEST_DELIMITER` (default `,`).

## 4. Workflow / pipeline

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 discover | `ingest_csv` pipeline | `root.rglob("*.csv")`, sorted | `list[Path]` | empty list, no error |
| 2 read | each path | `csv.DictReader`, check columns | rows | `IngestError data.ingest.missing_column` |
| 3 parse | each row | `_parse_row` → `Bar` | `Bar` | `IngestError data.ingest.malformed_row`; iterator stops |

Serves pipeline `ingest_csv`.

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `Bar` | `Bar(symbol, ts, open, high, low, close, volume)` | storage, prices, analysis | yes | — |
| `load_bars` | `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` | `ingest_csv` | no | `malformed_row`, `missing_column` |
| `discover_files` | `discover_files(root: Path) -> list[Path]` | `ingest_csv` | no | — |

## 6. Error handling and logging

`IngestError(DataError)` codes `data.ingest.missing_column`, `data.ingest.malformed_row`;
context carries `path` and, for a row, the row. Log `info` per file (`path`, `rows`),
`error` on raise, keys per `docs/architecture.md` **Shared conventions**.

## 7. Tests

Unit: a well-formed file; a missing column; a bad float; a bad timestamp; delimiter from
settings. Fixture: `tests/fixtures/ingest/aapl-3d.csv`.

## 8. Pitfalls and risks

1. Timestamps carry no offset; the parse yields a naive `datetime` (OQ-data-ingest-1).
2. A huge file read eagerly — mitigated by streaming rows.

## 9. Skills used

- `project-structure` — module sizes and `configs.py` placement.

## 10. Contract deviations

None.

## 11. Open questions

- OQ-data-ingest-1 — which zone are CSV timestamps in? Assumption: keep them naive and
  leave conversion to a later section.

## As shipped

`Bar.ts` shipped naive per OQ-data-ingest-1; review r1 approved. `_parse_row` inlined into
`load_bars`.

## Revision

None.
