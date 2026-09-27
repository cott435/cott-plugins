# Trade tape — architecture

Status: contracted
Updated: 2026-09-20

Fixture for the hooks eval set (`evals/sets/hooks.json`). Its presence is what puts a
directory in scope for every dev-team hook; the out-of-scope control directory has no
`docs/` at all.

## Goal

A clean, queryable copy of one analyst's trade export and a per-symbol VWAP summary
(`docs/brief.md`).

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | load trades, clean trades, store trades |

## Dependency graph

`data` has no in-repo dependency. `analysis` is in the brief and not yet contracted.

## Boundaries

`data` provides `Trade`: a mapping with the keys `ts`, `symbol`, `price`, `size`, `side`,
all strings; and a callable `load_trades(path) -> list[Trade]`.

## Shared conventions

- External sources: `dataset:trades` at `data/trades.csv`; no credential.
- Timezone: UTC everywhere.
- No convention yet for logging, config or CLI.

## Toolchain

| tool | command |
|---|---|
| tests | `python3 -m pytest packages/<pkg>` |
| lint | `ruff check packages/<pkg>` |
| format | `ruff format --check packages/<pkg>` |

## Non-goals

Live market data; charts.

## Open decisions

None.
