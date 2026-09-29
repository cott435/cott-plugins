# Architecture — trade tape

Contracted 2026-09-20 by `/dev-team:plan-repo` from `docs/brief.md`.

## Goal

A command-line research tool for one analyst: turn a CSV export of trades into a clean,
queryable SQLite copy, then compute a rolling VWAP per symbol and print a markdown summary.
No service, no scheduler, no network. Two packages, `data` below `analysis`.

## Packages

| package | responsibility | path | depends on | covers | candidate skills |
|---|---|---|---|---|---|
| `data` | load, clean and store the trade export; provide the stored trades to `analysis` | `packages/data` | — | load trades, clean trades, store trades (later: second export format) | — |
| `analysis` | rolling VWAP per symbol and the markdown summary, from the stored trades | `packages/analysis` | `data` | rolling VWAP, summary report | — |

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

- **Trades** — record sequence, `list[Trade]`; `Trade` is a frozen dataclass with `ts:
  datetime` (tz-aware UTC, non-null), `symbol: str` (non-null, upper-case), `price: float`
  (> 0), `size: int` (> 0), `side: "buy" | "sell"`. Invariants: sorted by `ts` ascending,
  no two records equal on all five fields. Provided by `data`'s public surface; consumed by
  `analysis/features`.

## Shared conventions

- Errors: each package has one exception base, `DataError` and `AnalysisError`, in
  `packages/<pkg>/src/<pkg>/errors.py`; a rejected input row raises with the row number and
  the field name in the message.
- Logging: stdlib `logging`, logger per module (`__name__`), no third-party logging.
- Config: env prefix `<PKG>_`, read with `os.environ` (no config library). `DATA_DB_PATH` —
  the SQLite file, default `./trades.sqlite`.
- Time: UTC everywhere. `ts` is parsed from ISO 8601 with a `Z` or `+00:00` offset; a naive
  timestamp is a rejected row.
- IDs: no convention — trades carry no id; a duplicate is a row equal on all five fields.
- CLI: `argparse`; one console script per package, named `<pkg>-<verb>`.
- External sources: `dataset:trades` at `data/trades.csv`, probed at repo scope —
  `docs/sources/trades.md` (**Access** readable). Constraining line: 400 rows, 2 exact
  duplicates and 1 out-of-order row; not a modeling dataset, so no split applies.

## Toolchain

- `uv` workspace; the root `pyproject.toml` lists `packages/*` as members.
- Tests: `uv run pytest packages/<pkg>`. Lint: `uv run ruff check`, `uv run ruff format
  --check`. Imports: `uv run lint-imports`. Docs: `uv run mkdocs build --strict`.
- Config in the root `pyproject.toml` (`[tool.ruff]`, `[tool.importlinter]`,
  `[tool.pytest.ini_options]`); `mkdocs.yml` at the root with `mkdocstrings`.
- No third-party runtime dependencies; SQLite through the standard library's `sqlite3`.

## Non-goals

- Live market data; charts; any network call; a scheduler.
- A Parquet export is *later* — do not rule it out, do not build it.

## Open decisions

- none
