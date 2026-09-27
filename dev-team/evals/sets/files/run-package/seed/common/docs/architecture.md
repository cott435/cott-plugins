# Trade tape — repo contract

Written: 2026-09-26 by `/dev-team:plan-repo`, from `docs/brief.md` (Status: ready, 2026-09-18).
Seeded for the `run-package` eval set: the shape `plan-repo` writes, filled by hand so the
driver's evals start at a planned package without a planning run of their own.

## Goal

One analyst, from the command line, turns a CSV export of trades into a clean SQLite copy and a
per-symbol VWAP summary in markdown. No service, no scheduler, no network.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | load trades, clean trades, store trades |
| `analysis` | `packages/analysis` | `data` | rolling VWAP, summary report |

## Dependency graph

```
analysis --> data
```

`data` has no upstream package. `analysis` imports `data`'s public surface only, never its
section modules.

## Boundaries

Shapes only; signatures live in each package contract.

| shape | fields | provided by | consumed by |
|---|---|---|---|
| `Trade` | `ts` (datetime, tz-aware UTC), `symbol` (str), `price` (float), `size` (int), `side` (`"buy"` or `"sell"`) — five fields, no more | `data` | `analysis` |
| `TradeStore` | a local SQLite file holding one `trades` table of `Trade` rows, unique on all five fields | `data` | `analysis`, read-only, through `data.load_trades` |

## Shared conventions

- Timezone: UTC everywhere; `ts` is parsed from ISO 8601 with a `Z` suffix and carried tz-aware.
- External sources: one dataset, `dataset:trades`, at `data/trades.csv` relative to the repo
  root; probe `docs/sources/trades.md`. The constraining line from the probe: the export holds
  two exact duplicate rows and one out-of-order timestamp, so ordering and uniqueness are
  `data`'s job and never assumed of the input.
- Configuration: environment variables, prefix `DATA_` for `data` and `ANALYSIS_` for
  `analysis`, read in each package's `configs.py` with `os.environ`; no third-party settings
  library (the brief allows no runtime dependency beyond the toolchain).
- Logging: the standard library `logging`, one logger per package named after it.
- CLI: `argparse`; one `[project.scripts]` entry per package pipeline.
- Errors: each package defines one base exception; a rejected input row names the data row
  number and the field.
- SQLite through the standard library's `sqlite3`.

## Toolchain

As `workspace-scaffold`: a `uv` workspace, one member per package under `packages/<pkg>` with
`src/<pkg>/`; `ruff`, `mypy --strict`, `pytest` with `pytest-cov`, `import-linter`,
`interrogate`, `mkdocs` with `mkdocstrings`. The quality bar is `docs/constraints.md`.

## Non-goals

- Live market data; charts.
- A second export format (later scope; the design must not rule it out).

## Open decisions

None.
