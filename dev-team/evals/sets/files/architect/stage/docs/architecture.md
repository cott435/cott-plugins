# Architecture — bar store

Contracted 2026-10-02 by `/dev-team:plan-repo` from `docs/brief.md`.

## Goal

A command-line research tool for one analyst: download ten years of daily price bars for 500
symbols from one vendor, keep a clean, queryable SQLite copy, then compute returns per symbol
and print a markdown summary. No service, no scheduler; the only network call is to the
vendor. Two packages, `data` below `analysis`.

## Packages

| package | responsibility | path | depends on | covers | candidate skills |
|---|---|---|---|---|---|
| `data` | download the vendor's daily bars, clean and validate them, and store them; provide the stored bars to `analysis` | `packages/data` | — | download bars, clean and validate bars, store bars (later: intraday bars) | — |
| `analysis` | daily and trailing returns per symbol and the markdown summary, from the stored bars | `packages/analysis` | `data` | returns, summary report | — |

## Dependency graph

```toml
[tool.importlinter]
root_packages = ["analysis", "data"]

[[tool.importlinter.contracts]]
name = "packages depend downward only"
type = "layers"
layers = ["analysis", "data"]
```

## Boundaries

### data → analysis

- **Bars** — record sequence, `list[Bar]`; `Bar` is a frozen dataclass with `symbol: str`
  (non-null, upper-case), `day: date` (a trading day), `open: float`, `high: float`,
  `low: float`, `close: float` (all > 0, `high` ≥ `open`, `close` ≥ `low`), `volume: int`
  (≥ 0). Invariants: sorted by `symbol`, then `day` ascending; one record per `symbol` and
  `day`. Provided by `data`'s public surface; consumed by `analysis/features`.

## Shared conventions

- Errors: each package has one exception base, `DataError` and `AnalysisError`, in
  `packages/<pkg>/src/<pkg>/errors.py`.
- Logging: stdlib `logging`, logger per module (`__name__`), no third-party logging.
- Config: env prefix `<PKG>_`, read with `os.environ` (no config library). `DATA_RAW_DIR` —
  where downloaded responses are kept, default `./var/raw`; raw daily bars are
  `<DATA_RAW_DIR>/bars/<symbol>.jsonl`, one vendor row per line. `DATA_DB_PATH` — the SQLite
  file, default `./bars.sqlite`. `BARFEED_API_KEY` — the vendor key, never logged.
- Time: UTC everywhere. A bar's `day` is the exchange's trading date, not a timestamp.
- IDs: a bar's key is (`symbol`, `day`).
- CLI: `argparse`; one console script per package, named `<pkg>-<verb>`.
- External sources: `api:barfeed`, probed at repo scope — `docs/sources/barfeed.md`
  (**Access** reachable). Constraining lines: 2,000 requests a day on the analyst's plan; a
  full pull of the universe is 5,000 requests.

## Toolchain

- `uv` workspace; the root `pyproject.toml` lists `packages/*` as members.
- Tests: `uv run pytest packages/<pkg>`. Lint: `uv run ruff check`, `uv run ruff format
  --check`. Imports: `uv run lint-imports`. Docs: `uv run mkdocs build --strict`.
- Config in the root `pyproject.toml` (`[tool.ruff]`, `[tool.importlinter]`,
  `[tool.pytest.ini_options]`); `mkdocs.yml` at the root with `mkdocstrings`.
- One third-party runtime dependency, `httpx`, in `data` only; SQLite through the standard
  library's `sqlite3`.

## Non-goals

- Live quotes, streaming, charts, a scheduler.
- Split and dividend adjustment: bars are the vendor's unadjusted rows.
- Intraday bars are *later* — do not rule them out, do not build them.

## Open decisions

- none
