# `data` — interface

The package's public surface, written by the `surface` section when `data` shipped
(2026-09-25). `data` ingests daily aggregate bars from polygon, cleans them into the repo
shape `BarTable`, lands one parquet file per run under `DATA_LANDING_DIR`, and records each
landed file as one row of the landing manifest.

## Public names

| name | kind | signature | providing module | consumer | since |
|---|---|---|---|---|---|
| `daily_pipeline` | function | `(run_date: date) -> Path` | `data.pipeline` | `features` | 2026-09-25 |

## Pipelines

`daily_pipeline(run_date)`: `ingest.fetch_bars` per symbol → `clean.clean_bars` → one parquet
file under `DATA_LANDING_DIR` → one `LandingManifest` row appended. Returns the parquet path.
A vendor failure ends the run with nothing landed.

## CLI commands

None.

## Configuration

`DATA_VENDOR_KEY`, `DATA_LANDING_DIR`. No defaults.

## Shapes provided

- `BarTable` — a `pandas.DataFrame` with columns `symbol: str`, `ts: datetime` (tz-aware UTC),
  `open`, `high`, `low`, `close: float`, `volume: int`; one row per symbol per session, sorted
  by `symbol, ts` (`docs/architecture.md` Boundaries).
- `LandingManifest` — one row per landed file, a `dict[str, Any]`, appended by `daily_pipeline`
  to `manifest.jsonl` under `DATA_LANDING_DIR`. Among its columns, `run_date` is the run's ISO
  date string and `rows` is the file's row count. The full column set, in order: see
  `packages/data/src/data/landing/manifest.py` (`MANIFEST_COLUMNS`).

## Deviations

None.

## Consumers (computed)

Snapshot, 2026-09-25: `features`.
