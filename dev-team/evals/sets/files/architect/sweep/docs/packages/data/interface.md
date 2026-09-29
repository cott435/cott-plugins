# `data` — interface

The public surface of `data` as shipped. 2026-09-26.

## Public names

| Name | Kind | Signature | Providing module | Consumer | Since |
|---|---|---|---|---|---|
| `Trade` | dataclass | `(ts: datetime, symbol: str, price: float, size: int, side: Literal["buy", "sell"])` | `data.ingest.model` | `analysis/features` | 2026-09-26 |
| `load_trades` | function | `(db_path: Path \| None = None) -> list[Trade]` | `data.storage.db` | `analysis/features` | 2026-09-26 |
| `DataError` | exception | base | `data.errors` | `data-ingest`, `analysis-summary` | 2026-09-26 |
| `TradeParseError` | exception | `(row: int, field: str, reason: str)` | `data.errors` | `data-ingest` | 2026-09-26 |

## Pipelines

`ingest` — `read_export` → `clean_trades` → `store_trades`; a `TradeParseError` stops the run
before anything is written, exit 1. Run by `data-ingest`.

## CLI commands

| Command | Entry point | Arguments | What it runs |
|---|---|---|---|
| `data-ingest` | `data.cli:ingest` | `csv` (path); `--db` (path, default `./trades.sqlite`) | the **ingest** pipeline |

## Configuration

`DATA_DB_PATH` (default `./trades.sqlite`), used by `load_trades` when no path is passed.

## Shapes provided

**Trades** (repo contract, Boundaries *data → analysis*): `list[Trade]` sorted by `ts`, no two
records equal on all five fields.

## Deviations

| Entry | Effect on the surface |
|---|---|
| `data/clean — 2026-09-24` (approved) | none: `dedupe` is internal |
| `docs/changes/side-aliases.md` (open) | none: aliases are normalized before `Trade` is built |

## Consumers (computed)

Snapshot 2026-09-26: no package under `packages/*/src` imports `data`; no
`docs/packages/*/contract.md` names `data` under **Consumes** (`analysis` is not yet planned).
