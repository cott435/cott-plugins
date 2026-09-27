# Package contract — `analysis`

Planned 2026-09-22 by `/dev-team:plan-package analysis` under `docs/architecture.md`.
Planned against `data` unshipped: every consumed name below is **provisional** (from
`docs/packages/data/contract.md`, not an `interface.md`).

## Purpose

`analysis` computes a rolling VWAP per symbol from the stored trades and prints a markdown
summary. Capabilities covered (`covers`):

- **rolling VWAP** — `features`. Brief: "Rolling volume-weighted average price per symbol over
  a window the user sets, computed from the stored trades via the data package's
  `load_trades`."
- **summary report** — `report`. Brief: "A markdown summary: one row per symbol with trade
  count, total size, last price and last VWAP."

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `features` | rolling VWAP per symbol over a user-set window of trades | `packages/analysis/src/analysis/features/` | `docs/packages/analysis/design/features.md` | — | — | — |
| `report` | one markdown row per symbol: count, total size, last price, last VWAP | `packages/analysis/src/analysis/report/` | `docs/packages/analysis/design/report.md` | — | `features` | — |
| `surface` | the package's pipelines (§4) and public surface (§5) | `packages/analysis/src/analysis/` | `docs/packages/analysis/design/surface.md` | — | `features`, `report` | — |

## Section interfaces

- `features` — `VwapPoint` (frozen dataclass: `symbol`, `ts`, `vwap: float`);
  `rolling_vwap(trades: list[Trade], window: int) -> list[VwapPoint]`, window in trades per
  symbol; `trades` is the **Trades** shape as `data.load_trades()` returns it.
- `report` — `summary(trades: list[Trade], points: list[VwapPoint]) -> str`, a markdown
  table, one row per symbol.

## Pipelines

- **summary** — trigger: `analysis-summary [--window N] [--db <path>]`. `data.load_trades()`
  → `list[Trade]` → `features.rolling_vwap` → `list[VwapPoint]` → `report.summary` → stdout.
  Failure: an empty tape prints a table with no rows and exits 0.

## Public surface (intent)

| name | realized by | consumer |
|---|---|---|
| `analysis-summary` (CLI) | pipeline **summary** | the analyst |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| `data` | `Trade` | **Trades** record | provisional |
| `data` | `load_trades` | `(db_path: Path \| None = None) -> list[Trade]`, every stored row sorted by `ts` | provisional |

## Package conventions

- `window` counts trades per symbol, not seconds.

## Open decisions

- none
