# Trade tape — repo contract

Written: 2026-09-26 by `/dev-team:plan-repo`, from `docs/brief.md` (Status: ready, 2026-09-18).
Seeded for the `run-package` eval set (evals 5 and 6): the shape `plan-repo` writes, filled by
hand, for a first slice of the brief whose `data` package has two independent sections.

## Goal

One analyst, from the command line, turns a CSV export of trades into validated `Trade`
records and lists the trading days the export covers. No service, no scheduler, no network.
This plan is the first slice of the brief: `clean trades`, `store trades` and the `analysis`
package are planned in a later change and are not part of this contract.

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| `data` | `packages/data` | — | load trades, trading sessions |

## Dependency graph

```
data
```

`data` has no upstream package.

## Boundaries

Shapes only; signatures live in each package contract.

| shape | fields | provided by | consumed by |
|---|---|---|---|
| `Trade` | `ts` (datetime, tz-aware UTC), `symbol` (str), `price` (float), `size` (int), `side` (`"buy"` or `"sell"`) — five fields, no more | `data` | the analyst, through `data`'s public surface |

## Shared conventions

- Timezone: UTC everywhere; `ts` is parsed from ISO 8601 with a `Z` suffix and carried tz-aware.
  A trading day is a UTC calendar date.
- External sources: one dataset, `dataset:trades`, at `data/trades.csv` relative to the repo
  root; probe `docs/sources/trades.md`. The constraining line from the probe: the export holds
  two exact duplicate rows and one out-of-order timestamp, so ordering and uniqueness are
  never assumed of the input.
- Configuration: environment variables, prefix `DATA_`, read in the package's `configs.py`
  with `os.environ`; no third-party settings library (the brief allows no runtime dependency
  beyond the toolchain).
- Logging: the standard library `logging`, one logger per package named after it.
- CLI: `argparse`; one `[project.scripts]` entry per package pipeline.
- Errors: each package defines one base exception; a rejected input row names the data row
  number and the field.

## Toolchain

As `workspace-scaffold`: a `uv` workspace, one member per package under `packages/<pkg>` with
`src/<pkg>/`; `ruff`, `mypy --strict`, `pytest` with `pytest-cov`, `import-linter`,
`interrogate`, `mkdocs` with `mkdocstrings`. The quality bar is `docs/constraints.md`.

## Non-goals

- Live market data; charts.
- An exchange holiday calendar: a trading day is a date the export holds a trade on, nothing
  more.
- A second export format (later scope; the design must not rule it out).

## Open decisions

None.
