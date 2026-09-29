# Architecture — venuedata

Written 2026-09-27 by `/dev-team:plan-repo`. Archived copy: `docs/history/2026-09-27-architecture.md`.

## Goal

Read the XVEN venue's daily trade exports into typed rows, and know which days the venue
traded, so `analysis` can work on complete sessions only.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | ingest, calendar |
| `analysis` | `packages/analysis` | `data` | features, report |

## Dependency graph

`analysis` → `data`. No cycles.

## Boundaries

Shapes crossing package boundaries, by name:

- **Trade** — one trade: `ts` (timezone-aware UTC datetime), `symbol` (str), `price` (float),
  `size` (int), `side` (`"buy"` or `"sell"`). Provided by `data`.
- **TradingDay** — a `datetime.date` on which XVEN held a session. Provided by `data`.

## Shared conventions

- Timezone: UTC everywhere (D1).
- Errors: each package raises subclasses of `ValueError` named `<Section>Error`; messages
  name the file and line where one applies, never the row's contents.
- Logging: `logging.getLogger("<pkg>.<section>")`, `INFO` per step, `extra=` keys only, never
  f-strings. Whether every record carries an `event` key is D3.
- External sources: none fetched. The venue's export files are dropped by hand into
  `data/raw/` at the repo root; they are large and never committed. Their dialect is the
  project skill `venue-csv` (`.claude/skills/venue-csv/`).
- Dependencies: standard library only in `data`, except what a decided `D<n>` adds.

## Toolchain

| item | value |
|---|---|
| language | Python 3.12 |
| package manager | `uv` workspace, `packages/*` |
| layout | `packages/<pkg>/src/<pkg>/<section>/` |
| tests | `pytest`; one package: `uv run pytest packages/<pkg>`; unit tests under `packages/<pkg>/tests/unit/<section>/`, intent tests under `packages/<pkg>/tests/intent/<section>/` |
| lint / format | `uv run ruff check`, `uv run ruff format --check` |
| types | `uv run mypy --strict packages/<pkg>/src` |
| imports | `uv run lint-imports` |
| docs | `uv run mkdocs build --strict` |

## Non-goals

Fetching exports from the venue; any venue but XVEN; intraday updates.

## Open decisions

- D1 — decided (UTC).
- D2 — decided (`python-dateutil` for `TradeTime`).
- D3 — open; its assumption stands.
