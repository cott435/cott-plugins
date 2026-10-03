# `data` — package contract

Written 2026-10-02 by /dev-team:plan-package data.

## Purpose

Ingests daily aggregate bars from polygon, cleans them into the repo shape `BarTable`, and
provides the `daily` pipeline the `features` package and the `data-daily` command run.
Provides: `BarTable`. Covers `daily-bars` — section `ingest` and `clean`; brief Notes: "one
vendor, daily bars only, adjusted prices".

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | fetches one symbol's daily aggregate bars from polygon for a date range and parses the payload into `Bar` rows; owns the vendor client | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `api:polygon` |
| `clean` | validates and de-duplicates `Bar` rows across symbols into a `BarTable` | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | the package's public surface: the `daily` pipeline (§4), the `data-daily` command, the settings, and every public name (§6), built to the frames §5 fixes. Its design is written right after PLAN, from this contract — **Section interfaces**, **Pipelines**, **Public surface (intent)** and **Call paths** — before any sibling is built, and its code is built last, from the shipped READMEs; its README is `docs/packages/data/interface.md`. | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

- `ingest` → `Bar` (frozen dataclass, one session of one symbol; its fields are `BarTable`'s
  columns, `docs/architecture.md` Boundaries), `IngestError(reason: str, symbol: str)`,
  `VendorClient` (a `Protocol`: `get(self, path: str, params: dict[str, str]) -> dict[str, Any]`,
  raising `VendorError(status: int)` on any non-2xx response), `VendorError(status: int)`,
  `PolygonClient(api_key: str, base_url: str)` — the `VendorClient` for `api:polygon`; its
  `get(path, params) -> dict[str, Any]` is the frame `ingest.PolygonClient.get` below and makes
  the vendor call —
  `parse_bars(payload, symbol) -> tuple[Bar, ...]`,
  `fetch_bars(symbol, start, end, *, client, retries=3) -> tuple[Bar, ...]`.
- `clean` → `clean_bars(bars: Iterable[Bar]) -> BarTable`.
- `surface` → `daily_pipeline(run_date) -> Path` (the function the `daily` pipeline names,
  `pipelines.daily_pipeline`), `main(argv=None) -> int` (the `data-daily` command function,
  `cli.main`; the console script calls it), `DataSettings` (the package settings, read from the
  environment), `DataError(reason: str, detail: str)`.

## Pipelines

- `daily` — function `pipelines.daily_pipeline`; trigger: the `data-daily` command (`cli.main`)
  with `--run-date`. One `ingest.PolygonClient` built from `DATA_VENDOR_KEY`;
  `ingest.fetch_bars` per symbol of `DATA_SYMBOLS`, a one-day range (`run_date` to `run_date`)
  → `tuple[Bar, ...]` each → `clean.clean_bars` over every symbol's rows together → `BarTable`
  → one CSV file `<DATA_LANDING_DIR>/<run_date>.csv`, columns in `BarTable` order. Failure: an
  `IngestError` for one symbol aborts the run; nothing is written.

## Call paths

- `data-daily` (budget 8):
  - vendor call: 1 `cli.main` → 2 `pipelines.daily_pipeline` → 3 `ingest.fetch_bars` → 4 `ingest.PolygonClient.get` → `urllib.request.urlopen`
  - file write: 1 `cli.main` → 2 `pipelines.daily_pipeline` → `DataFrame.to_csv`

## Public surface (intent)

| name | realized by | consumer |
|---|---|---|
| `BarTable` (shape) | `clean` | `features` |
| `daily_pipeline(run_date) -> Path` | `surface` | the `data-daily` command; `features` |
| `data-daily` (command; `cli.main`, console script `data-daily`) | `surface` | the operator |

Nothing from `ingest` or `clean` is public; every public name is `from data import <name>`.

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Vendor payloads are never persisted by `ingest`; landing is `clean`'s and the pipeline's.
- Settings come from the environment, read once per run by `surface`: `DATA_VENDOR_KEY`
  (required), `DATA_SYMBOLS` (required; comma-separated tickers), `DATA_LANDING_DIR`
  (required; a directory), `DATA_BASE_URL` (default `https://api.polygon.io`).
- A landing file is `<DATA_LANDING_DIR>/<run_date>.csv` with a header row in `BarTable` column
  order and no index column.

## Open decisions

- D1 — decided: timestamps tz-aware UTC.
- D2 — open: zero-volume bars (scope `data/ingest`).
